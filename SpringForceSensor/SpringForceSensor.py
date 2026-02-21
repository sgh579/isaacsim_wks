import omni.usd
import omni.physx
import numpy as np
from pxr import Usd, UsdGeom, Gf, UsdPhysics, PhysxSchema
import isaacsim.core.utils.prims as prim_utils

class SpringForceSensor:
    def __init__(self, prim_path, stiffness=1000.0, damping=1000.0):
        self.prim_path = prim_path
        self.base_path = f"{prim_path}/Base"
        self.ee_path = f"{prim_path}/EndEffector"
        self.joint_path = f"{prim_path}/SpringJoint"
        
        self.k = stiffness
        self.c = damping
        
        self._build_sensor_hierarchy()

    def _build_sensor_hierarchy(self):
        stage = omni.usd.get_context().get_stage()
        
        # 1. 创建 Base (Cube)
        self.base_prim = prim_utils.create_prim(
            self.base_path, "Cube", 
            translation=(0, 0, 3.0), scale=(0.05, 0.05, 1)
        )
        # --- 参考示例的 Kinematic 写法 ---
        UsdPhysics.CollisionAPI.Apply(self.base_prim)
        physicsAPI = UsdPhysics.RigidBodyAPI.Apply(self.base_prim)
        # 核心：创建并设置 Kinematic 属性为 True
        physicsAPI.CreateKinematicEnabledAttr().Set(True)
        
        # 获取平移操作句柄，方便后续 update_base_pose 调用
        cube_geom = UsdGeom.Cube(self.base_prim)
        self.translate_op = cube_geom.GetOrderedXformOps()[0] if cube_geom.GetOrderedXformOps() else cube_geom.AddTranslateOp()

        # 2. 创建 EndEffector (Sphere) - 动态刚体
        self.ee_prim = prim_utils.create_prim(
            self.ee_path, "Sphere", 
            translation=(0, 0, 2.0), scale=(0.1, 0.1, 0.1)
        )
        UsdPhysics.CollisionAPI.Apply(self.ee_prim)
        UsdPhysics.RigidBodyAPI.Apply(self.ee_prim)
        UsdPhysics.MassAPI.Apply(self.ee_prim).GetMassAttr().Set(0) # unsuccessful, can't cancel the inertia

        # 3. 创建 D6 Joint 并配置约束
        d6_joint = UsdPhysics.Joint.Define(stage, self.joint_path)
        d6_joint.CreateBody0Rel().SetTargets([self.base_path])
        d6_joint.CreateBody1Rel().SetTargets([self.ee_path])
        
        # 本地锚点：Joint 在 Base 下方 1m 处，EE 在其中心
        d6_joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0, 0, -1))
        d6_joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
        
        d6_prim = d6_joint.GetPrim()

        # 锁死旋转轴
        for axis in [UsdPhysics.Tokens.rotX, UsdPhysics.Tokens.rotY, UsdPhysics.Tokens.rotZ]:
            limit = UsdPhysics.LimitAPI.Apply(d6_prim, axis)
            limit.CreateLowAttr(1.0)
            limit.CreateHighAttr(-1.0)

        # 配置平移轴弹簧 (Linear Drive)
        for axis in ["transX", "transY"]:
            drive = UsdPhysics.DriveAPI.Apply(d6_prim, axis)
            drive.CreateTypeAttr("force")
            drive.CreateStiffnessAttr(self.k)
            drive.CreateDampingAttr(self.c)
            drive.CreateTargetPositionAttr(0.0)

        axis = "transZ"
        drive = UsdPhysics.DriveAPI.Apply(d6_prim, axis)
        drive.CreateTypeAttr("force")
        drive.CreateStiffnessAttr(self.k)
        drive.CreateDampingAttr(self.c)
        drive.CreateTargetPositionAttr(-0.3)

    def update_base_pose(self, position):
        """
        参考示例中动画更新的方式，直接操作 TranslateOp
        position: (x, y, z)
        """
        self.translate_op.Set(Gf.Vec3d(*position))

    def get_equivalent_force_geom(self):
        """方案一：几何位移解算法 (F = K * delta_x)"""
        base_pose = omni.usd.get_world_transform_matrix(self.base_prim)
        ee_pose = omni.usd.get_world_transform_matrix(self.ee_prim)
        
        # 转换到局部坐标系
        ee_local_pos = base_pose.GetInverse().Transform(ee_pose.ExtractTranslation())
        delta_x = ee_local_pos - Gf.Vec3d(0, 0, -1.3)
        
        return np.array([delta_x[0], delta_x[1], delta_x[2]]) * self.k

    def get_equivalent_force_physx(self):
        """方案二：物理引擎反馈法 (PhysX Reaction Force)"""
        physx_interface = omni.physx.get_physx_interface()
        force_data = physx_interface.get_joint_forces(self.joint_path)
        return np.array(force_data[:3]) if force_data else np.zeros(3)