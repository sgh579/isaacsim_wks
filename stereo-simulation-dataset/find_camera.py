# 必须先启动 SimulationApp 才能加载相关模块
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

import importlib
import inspect

def check_stereo_camera():
    module_name = "isaacsim.sensors.camera"
    class_to_find = "StereoCamera"
    
    print(f"\n" + "="*50)
    print(f"正在检查模块: {module_name}")
    
    try:
        # 尝试动态导入模块
        module = importlib.import_module(module_name)
        
        # 检查类是否存在
        if hasattr(module, class_to_find):
            print(f"✅ 成功! 找到了类: {class_to_find}")
        else:
            print(f"❌ 失败: 在 {module_name} 中找不到 '{class_to_find}'")
            
            # 列出该模块下所有可用的类，看看真相是什么
            print("\n该模块下可用的所有类/成员如下:")
            members = inspect.getmembers(module, inspect.isclass)
            for name, _ in members:
                print(f" - {name}")
                
    except ImportError as e:
        print(f"无法导入模块 {module_name}: {e}")
    
    print("="*50 + "\n")

check_stereo_camera()
simulation_app.close()

# result: gemini is also cjb
# ==================================================
# 正在检查模块: isaacsim.sensors.camera
# ❌ 失败: 在 isaacsim.sensors.camera 中找不到 'StereoCamera'

# 该模块下可用的所有类/成员如下:
#  - BaseSensor
#  - Camera
#  - CameraView
#  - Extension
#  - IsaacRtxLidarSensorAPI
#  - SingleViewDepthSensor
#  - SingleViewDepthSensorAsset
#  - SingleXFormPrim
# ==================================================
