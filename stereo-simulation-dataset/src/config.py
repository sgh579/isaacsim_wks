import os
import numpy as np

class Config:
    # --- 1. 路径管理 ---
    # 自动获取当前文件所在目录，确保无论在哪里启动，路径都可预测
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 默认保存到主目录下的 output 文件夹
    OUTPUT_DIR = os.path.join(BASE_DIR, "output", "stereo_dataset_geometry_shape")
    # OUTPUT_DIR = os.path.join(BASE_DIR, "output", "stereo_dataset_bunny")
    
    # --- 2. 相机配置 ---
    RESOLUTION = (400, 400)
    FOCAL_LENGTH = 1.32383  # 单位: mm (Isaac Sim Camera API 使用)
    BASELINE = 0.032     # 双目基线距离 (m)
    
    # --- 3. 轨迹模式配置 ---
    # 选项: "circle" 或 "linear"
    ORBIT_MODE = "linear" 
    # ORBIT_MODE = "circle" 
    
    NUM_FRAMES = 50
    RADIUS = 0.4        # 圆形轨道的半径 或 直线轨道的偏移范围
    HEIGHT = 0.4        # 相机高度
    TARGET_POINT = np.array([0.0, 0.0, 0.0])

    POINTA = np.array([0.5, 0.5, 0.5])
    POINTB = np.array([0.2, 0.2, 0.2])
    
    # --- 4. 场景物体配置 ---
    # 选项: "diy" (内置几何体) 或 "import" (加载外部模型)
    # SCENE_MODE = "import"
    SCENE_MODE = "diy"
    
    # DIY 模式参数
    SPHERE_RADIUS = 0.1
    CUBE_SCALE = [0.05, 0.05, 0.1]
    CUBE_POS = [0.12, -0.12, 0.1]
    
    # IMPORT 模式参数 (如果 SCENE_MODE == "import")
    USD_PATH = os.path.join(BASE_DIR, "asset", "bunny.obj")
    # USD_PATH = "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/2023.1.1/Isaac/Samples/Props/Stanford_Bunny/stanford_bunny.usd"
        # 模型调整：Bunny 通常很小，可能需要放大，且位置需要贴地
    MODEL_SCALE = [2, 2, 2]  # 根据需要调整
    MODEL_POS = [0.0, 0.0, 0.0]    # 放置在原点

    @classmethod
    def prepare_output_dirs(cls):
        """在 main.py 调用，自动创建所需的文件夹结构"""
        left_dir = os.path.join(cls.OUTPUT_DIR, "left")
        right_dir = os.path.join(cls.OUTPUT_DIR, "right")
        os.makedirs(left_dir, exist_ok=True)
        os.makedirs(right_dir, exist_ok=True)
        return left_dir, right_dir