from omni.isaac.kit import SimulationApp
# 必须先启动，否则 Manager 无法初始化
simulation_app = SimulationApp({"headless": True})

import omni.kit.app
import omni.ext

# 获取 App 接口和扩展管理器
manager = omni.kit.app.get_app_interface().get_extension_manager()

# 检查 omni.physx 是否启用并获取其版本
# 在新版本中，建议通过 get_enabled_extension_id 获取完整的标识符
ext_id = manager.get_enabled_extension_id("omni.physx")

if ext_id:
    # 从扩展字典中提取版本信息
    ext_dict = manager.get_extension_dict(ext_id)
    version = ext_dict.get("version", "Unknown")
    path = ext_dict.get("path", "Unknown")
    print(f"--- Component Info ---")
    print(f"PhysX Extension ID: {ext_id}")
    print(f"PhysX Version: {version}")
    print(f"PhysX Path: {path}") # 这将直接告诉你它的物理位置
else:
    print("omni.physx extension is not enabled or found.")

simulation_app.close()

# the result
# [6.797s] Simulation App Startup Complete

# --- Component Info ---

# PhysX Extension ID: omni.physx-107.3.26

# PhysX Version: Unknown

# PhysX Path: /home/goodmansun/isaacsim/_build/linux-x86_64/release/extscache/omni.physx-107.3.26+107.3.3.lx64.r.cp311.u353

# [6.864s] Simulation App Shutting Down