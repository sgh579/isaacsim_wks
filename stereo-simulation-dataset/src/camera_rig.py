import numpy as np
from pxr import Gf
from isaacsim.sensors.camera import Camera

class StereoRig:
    def __init__(self, resolution, focal_length, baseline):
        self.baseline = baseline
        self.cam_l = Camera(prim_path="/World/cam_l", resolution=resolution)
        self.cam_r = Camera(prim_path="/World/cam_r", resolution=resolution)
        
        for cam in [self.cam_l, self.cam_r]:
            cam.initialize()
            cam.set_focal_length(focal_length)
            # 设置剪切平面，防止物体太近或太远被裁剪
            cam.set_clipping_range(near_distance=0.01, far_distance=10000.0)

    def _get_rig_orientation(self, eye_pos, target_pos):
        """计算修正后的四元数，确保相机朝向正确且画面水平"""
        eye = Gf.Vec3d(*eye_pos.tolist())
        target = Gf.Vec3d(*target_pos.tolist())
        up = Gf.Vec3d(0, 0, 1)
        
        lookat_m = Gf.Matrix4d().SetLookAt(eye, target, up)
        cam_matrix = lookat_m.GetInverse()
        
        # Isaac Sim 惯例修正：
        # 1. 绕Y轴转90度使+X指向目标
        # 2. 绕X轴转-90度修正图像翻转
        combined_rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90) * Gf.Rotation(Gf.Vec3d(0, 1, 0), 90)
        correction = Gf.Matrix4d().SetRotate(combined_rot)
        
        final_matrix = correction * cam_matrix
        q = final_matrix.ExtractRotationQuat()
        return np.array([q.GetReal(), *q.GetImaginary()]) # 返回 [w, x, y, z]

    def set_stereo_pose(self, center_pos, target_point):
        """设置双目相机位姿（平行光轴配置）"""
        rig_quat = self._get_rig_orientation(center_pos, target_point)
        
        # 计算水平面上的视线方向，用于推导侧向向量（Side Vector）
        view_dir_h = np.array([center_pos[0], center_pos[1], 0])
        dist_h = np.linalg.norm(view_dir_h)
        
        if dist_h > 1e-6:
            view_dir_h /= dist_h
            # 侧向向量（与视线和Up轴垂直）
            side_vec = np.array([-view_dir_h[1], view_dir_h[0], 0])
        else:
            side_vec = np.array([0, 1, 0])
        
        # 计算左右相机位置
        pos_l = center_pos + side_vec * (self.baseline / 2.0)
        pos_r = center_pos - side_vec * (self.baseline / 2.0)
        
        self.cam_l.set_world_pose(position=pos_l, orientation=rig_quat)
        self.cam_r.set_world_pose(position=pos_r, orientation=rig_quat)
        
        return pos_l, pos_r, rig_quat

    def capture(self):
        """获取最新的 RGBA 图像"""
        return self.cam_l.get_rgba(), self.cam_r.get_rgba()