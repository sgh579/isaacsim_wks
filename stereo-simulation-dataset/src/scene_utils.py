import isaacsim.core.utils.prims as prim_utils
from pxr import UsdLux, Sdf

def setup_stereo_scene(world, config):
    """根据 Config 配置初始化场景"""
    world.scene.add_default_ground_plane()
    stage = prim_utils.get_current_stage()
    
    # 1. 设置灯光
    UsdLux.DomeLight.Define(stage, "/World/DomeLight").CreateIntensityAttr(1200.0)
    dist_light = UsdLux.DistantLight.Define(stage, "/World/DistantLight")
    dist_light.CreateIntensityAttr(2000.0)
    dist_light.AddRotateXYZOp().Set((45, 0, 45))

    # 2. 根据模式放置物体
    if config.SCENE_MODE == "diy":
        # 放置球体
        prim_utils.create_prim(
            "/World/obj_sphere", "Sphere", 
            translation=(0.0, 0.0, config.SPHERE_RADIUS), 
            attributes={"radius": config.SPHERE_RADIUS}
        )
        # 放置立方体
        prim_utils.create_prim(
            "/World/obj_cube", "Cube", 
            translation=tuple(config.CUBE_POS), 
            scale=tuple(config.CUBE_SCALE)
        )
        print(">>> Scene: DIY (Sphere + Cube) loaded.")

    elif config.SCENE_MODE == "import":
        # 导入模型并应用缩放和位移
        prim_utils.create_prim(
            "/World/imported_model", 
            usd_path=config.USD_PATH,
            translation=tuple(config.MODEL_POS),
            scale=tuple(config.MODEL_SCALE) # 必须加入 scale 参数
        )
        print(f">>> Scene: Stanford Bunny loaded from: {config.USD_PATH}")