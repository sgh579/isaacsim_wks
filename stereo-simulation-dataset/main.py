# 主入口，控制仿真循环
from isaacsim import SimulationApp

# 1. 必须在任何 Isaac Sim 核心组件导入前启动
# 根据 Config 设置选择是否开启 headless (无界面) 模式
simulation_app = SimulationApp({"headless": False})

import numpy as np
from isaacsim.core.api import World

# 导入你拆分好的模块
from src.config import Config
from src.camera_rig import StereoRig
from src.scene_utils import setup_stereo_scene
from src.data_handler import DatasetWriter

def calculate_trajectory(frame_idx, total_frames, config):
    """根据配置计算当前帧相机的中心点位置"""
    if config.ORBIT_MODE == "circle":
        # 圆形轨道逻辑
        angle = np.radians((frame_idx / total_frames) * 360)
        x = config.RADIUS * np.cos(angle)
        y = config.RADIUS * np.sin(angle)
        return np.array([x, y, config.HEIGHT])
    
    elif config.ORBIT_MODE == "linear":
        # 计算当前进度：0.0 表示第 0 帧（点 A），1.0 表示最后一帧（点 B）
        # 使用 total_frames - 1 是为了确保最后一帧刚好落在 POINTB 上
        progress = frame_idx / (total_frames - 1)
        
        # 线性插值公式：A + (B - A) * t
        current_pos = config.POINTA + (config.POINTB - config.POINTA) * progress
        
        return current_pos
    
    else:
        raise ValueError(f"Unknown ORBIT_MODE: {config.ORBIT_MODE}")

def main():
    # 2. 初始化物理世界
    world = World(stage_units_in_meters=1.0)
    
    # 3. 准备输出目录 (利用你刚学的 @classmethod)
    left_dir, right_dir = Config.prepare_output_dirs()
    
    # 4. 构建场景 (DIY 几何体 或 导入外部模型)
    setup_stereo_scene(world, Config)
    
    # 5. 初始化相机系统 (双目基线、焦距等)
    rig = StereoRig(
        resolution=Config.RESOLUTION, 
        focal_length=Config.FOCAL_LENGTH, 
        baseline=Config.BASELINE
    )
    
    # 6. 初始化数据记录器
    writer = DatasetWriter(Config.OUTPUT_DIR)
    intrinsic_k = rig.cam_l.get_intrinsics_matrix()
    writer.save_metadata(Config, intrinsic_k)
    
    # 重置世界以应用更改
    world.reset()
    
    # 预热渲染器：让光照和纹理加载完毕，避免第一帧黑屏
    print(">>> Warming up renderer...")
    for _ in range(30):
        world.step(render=True)

    print(f">>> Starting capture in {Config.ORBIT_MODE} mode...")

    try:
        for i in range(Config.NUM_FRAMES):
            # A. 计算相机中心位置
            center_pos = calculate_trajectory(i, Config.NUM_FRAMES, Config)
            
            # B. 更新双目相机位姿 (内部处理 look-at 和基线偏移)
            pos_l, pos_r, quat = rig.set_stereo_pose(center_pos, Config.TARGET_POINT)
            
            # C. 仿真步进并渲染
            world.step(render=True)
            simulation_app.update()
            
            # D. 提取图像数据
            img_l, img_r = rig.capture()
            
            # E. 保存数据
            if img_l is not None and img_r is not None:
                writer.write_frame(
                    frame_id=i, 
                    time=world.current_time, 
                    pos_l=pos_l, 
                    pos_r=pos_r, 
                    quat=quat, 
                    img_l=img_l, 
                    img_r=img_r
                )
            
            if i % 10 == 0:
                print(f"Captured {i}/{Config.NUM_FRAMES} frames...")

    except Exception as e:
        print(f"An error occurred during simulation: {e}")
    
    finally:
        # 7. 清理工作
        writer.close()
        print(f">>> Task finished. Data saved to: {Config.OUTPUT_DIR}")
        # while True:
        #     world.step(render=True)
        #     simulation_app.update()
        simulation_app.close()



if __name__ == "__main__":
    main()