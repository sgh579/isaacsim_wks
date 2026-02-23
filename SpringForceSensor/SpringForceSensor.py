import omni.usd
import omni.physx
import numpy as np
from pxr import Usd, UsdGeom, Gf, UsdPhysics, PhysxSchema, Sdf
import isaacsim.core.utils.prims as prim_utils

class SpringForceSensor:
    def __init__(self, prim_path, stiffness=100.0, damping=10.0, probe_mass=0.0001, t_base = [0.0, 0.0, 3.0]):
        self.prim_path = prim_path
        self.base_path = f"{prim_path}/Base"
        self.ee_path = f"{prim_path}/EndEffector"
        self.joint_path = f"{prim_path}/SpringJoint"
        
        self.k = stiffness
        self.c = damping
        self.probe_mass = probe_mass

        # 几何参数
        self.t_base = t_base
        # 我们不再直接缩放 Base 刚体，而是将其 Scale 保持为 1,1,1
        self.base_dims = [0.05, 0.05, 0.2] # 目标半长
        self.l_0 = 0.4
        self.t_probe = t_base
        self.t_probe[2] -= self.l_0
        # self.t_probe = [0.0, 0.0, self.t_base[2] - self.l_0]
        self.s_probe = [0.1, 0.1, 0.1]
        
        self._build_sensor_hierarchy()

    def _build_sensor_hierarchy(self):
        stage = omni.usd.get_context().get_stage()
        
        # 1. 创建 Base 刚体 (使用 Xform 而不是 Cube)
        # 核心：Scale 必须是 (1, 1, 1)，这样本地坐标系 1单位 = 1米
        self.base_prim = prim_utils.create_prim(
            self.base_path, "Xform", 
            translation=tuple(self.t_base), scale=(1.0, 1.0, 1.0)
        )
        physicsAPI = UsdPhysics.RigidBodyAPI.Apply(self.base_prim)
        physicsAPI.CreateKinematicEnabledAttr().Set(True)

        # 为 Base 添加视觉和碰撞几何体 (作为子级)
        # 这样缩放只影响外观，不影响 Base 刚体本身的物理坐标系
        base_visual_path = f"{self.base_path}/Visual"
        prim_utils.create_prim(
            base_visual_path, "Cube",
            scale=tuple(self.base_dims) # 缩放仅作用于子级
        )

        # 获取平移句柄
        base_xform = UsdGeom.Xform(self.base_prim)
        self.translate_op = base_xform.GetOrderedXformOps()[0] if base_xform.GetOrderedXformOps() else base_xform.AddTranslateOp()

        # 2. 创建 EndEffector (Sphere)
        self.ee_prim = prim_utils.create_prim(
            self.ee_path, "Sphere", 
            translation=tuple(self.t_probe), scale=tuple(self.s_probe)
        )
        UsdPhysics.CollisionAPI.Apply(self.ee_prim)
        UsdPhysics.RigidBodyAPI.Apply(self.ee_prim)
        UsdPhysics.MassAPI.Apply(self.ee_prim).GetMassAttr().Set(self.probe_mass)

        # 3. 创建 D6 Joint
        d6_joint = UsdPhysics.Joint.Define(stage, self.joint_path)
        d6_joint.CreateBody0Rel().SetTargets([self.base_path])
        d6_joint.CreateBody1Rel().SetTargets([self.ee_path])
        
        # 排除内部碰撞
        d6_joint.CreateExcludeFromArticulationAttr().Set(True)
        
        # 锚点：因为 Base 没缩放，这里的 (0,0,0) 就是真正的中心点
        d6_joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
        d6_joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
        
        d6_prim = d6_joint.GetPrim()

        # 锁死旋转并【清除 0.04 缓冲区】
        for axis in [UsdPhysics.Tokens.rotX, UsdPhysics.Tokens.rotY, UsdPhysics.Tokens.rotZ]:
            limit = UsdPhysics.LimitAPI.Apply(d6_prim, axis)
            limit.CreateLowAttr(1.0)
            limit.CreateHighAttr(-1.0)
            d6_prim.CreateAttribute(f"physxJoint:{axis}:contactDistance", Sdf.ValueTypeNames.Float).Set(0.0)

        # 配置平移轴 (清理 transZ 缓冲区)
        for axis in ["transX", "transY", "transZ"]:
            drive = UsdPhysics.DriveAPI.Apply(d6_prim, axis)
            drive.CreateTypeAttr("force")
            drive.CreateStiffnessAttr(self.k)
            drive.CreateDampingAttr(self.c)
            
            target = -self.l_0 if axis == "transZ" else 0.0
            drive.CreateTargetPositionAttr(target)
            
            # 清除平移轴的 0.04 干扰
            d6_prim.CreateAttribute(f"physxJoint:{axis}:contactDistance", Sdf.ValueTypeNames.Float).Set(0.0)

    def get_equivalent_force_geom(self):
        """现在 Scale=1，矩阵运算的结果将直接以 '米' 为单位"""
        base_pose = omni.usd.get_world_transform_matrix(self.base_prim)
        ee_pose = omni.usd.get_world_transform_matrix(self.ee_prim)
        
        # 此时的 GetInverse() 不包含缩放，计算非常纯净
        ee_local_pos = base_pose.GetInverse().Transform(ee_pose.ExtractTranslation())

        # 理想位置就在 (0, 0, -0.4)
        target_local_pos = Gf.Vec3d(0, 0, -self.l_0)
        delta_x = ee_local_pos - target_local_pos
        
        # 调试打印：你会发现这次 delta_x 终于接近 0 了
        # print(f"DEBUG: ee_local={ee_local_pos}, target={target_local_pos}, delta={delta_x}")
        
        return np.array([delta_x[0], delta_x[1], delta_x[2]]) * self.k
    def update_base_pose(self, position):
        """更新 Base 的世界坐标位置"""
        self.translate_op.Set(Gf.Vec3d(*position))