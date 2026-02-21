from isaacsim import SimulationApp
import os
import csv
from datetime import datetime

# 1. 启动 App
simulation_app = SimulationApp({"headless": False})

from SpringForceSensor import SpringForceSensor
import isaacsim.core.utils.prims as prim_utils
from isaacsim.core.api import World
from omni.physx.scripts import deformableUtils, physicsUtils
from pxr import UsdGeom, Gf, PhysxSchema
import omni.kit.commands
import omni.usd
import numpy as np

# 2. 初始化世界
world = World(stage_units_in_meters=1.0)
stage = omni.usd.get_context().get_stage()

scene = world.get_physics_context()
scene.enable_gpu_dynamics(True)
# scene.set_solver_position_iteration_count(64) # 针对高精度变形强制增加 # invalid
scene.set_broadphase_type("GPU")

def create_deformable_box_official_style(target_path="/World/Sponge"):
    _, tmp_path = omni.kit.commands.execute("CreateMeshPrim", prim_type="Cube", select_new_prim=False)
    omni.kit.commands.execute("MovePrim", path_from=tmp_path, path_to=target_path)
    mesh = UsdGeom.Mesh.Get(stage, target_path)
    mesh.GetPrim().GetAttribute("xformOp:translate").Set(Gf.Vec3f(0.0, 0.0, 0.5))
    mesh.GetPrim().GetAttribute("xformOp:scale").Set(Gf.Vec3f(1.0, 1.0, 1.0))
    mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)

    deformableUtils.add_physx_deformable_body(
        stage, mesh.GetPath(),
        collision_simplification=False,
        simulation_hexahedral_resolution=100, 
        self_collision=True,
    )

    deformableUtils.add_deformable_body_material(
        stage, target_path + "Material",
        youngs_modulus=30000.0, poissons_ratio=0.45,
        damping_scale=0.0, dynamic_friction=0.5,
    )
    physicsUtils.add_physics_material_to_prim(stage, mesh.GetPrim(), target_path + "Material")
    return mesh

# 3. 执行场景搭建
# create_deformable_box_official_style()
world.scene.add_default_ground_plane()
sensor = SpringForceSensor("/World/Sensor")

# --- 运动参数配置 ---
start_z = 2.4    
end_z = 2.1      
speed = 0.1      
wait_time = 5.0  # 前 5s 静止

total_distance = abs(start_z - end_z)
move_duration = total_distance / speed
move_direction = -1.0 if end_z < start_z else 1.0

# --- CSV 路径与命名 ---
save_dir = os.path.expanduser("~/Documents/ExperimentalDataRaw/press")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(save_dir, f"{timestamp}.csv")

# 4. 重置世界
world.reset()

print(f"--- 仿真准备就绪 ---")
print(f"模式：等待 {wait_time}s 后开始运动并记录")
print(f"目标：{start_z}m -> {end_z}m (时长: {move_duration:.2f}s)")

csv_file = None
csv_writer = None

# 5. 主循环
try:
    while simulation_app.is_running():
        current_time = world.current_time
        
        # --- 运动与控制逻辑分段 ---
        if current_time <= wait_time:
            # A. 静止阶段
            target_z = start_z
            status = "WAITING"
        elif current_time <= (wait_time + move_duration):
            # B. 运动阶段
            elapsed_move_time = current_time - wait_time
            target_z = start_z + (move_direction * speed * elapsed_move_time)
            status = "MOVING"
        else:
            # C. 保持阶段
            target_z = end_z
            status = "FINISHED"

        # 更新位置
        sensor.update_base_pose(position=(0, 0, target_z))
        world.step(render=True)

        # --- 数据采集与记录逻辑 ---
        # 仅在静止时间结束后开始记录 CSV
        if current_time > wait_time:
            # 首次进入记录阶段时打开文件
            if csv_file is None:
                csv_file = open(csv_filename, mode='w', newline='')
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['time', 'f_x', 'f_y', 'f_z', 'base_z'])
                print(f"--- 开始记录数据至: {csv_filename} ---")

            f_geom = sensor.get_equivalent_force_geom()
            # 记录相对于运动开始的时间（或者原始时间，取决于你的分析需求，这里用原始时间）
            csv_writer.writerow([round(current_time, 4), f_geom[0], f_geom[1], f_geom[2], round(target_z, 4)])

        # 终端打印
        if int(current_time * 100) % 20 == 0:
            f_val = sensor.get_equivalent_force_geom()[2] if current_time > wait_time else 0.0
            print(f"[{status}] T: {current_time:.1f}s | Z: {target_z:.3f} | Fz: {f_val:.4f} N")

except Exception as e:
    print(f"错误: {e}")

finally:
    if csv_file:
        csv_file.close()
    print(f"--- 任务完成，文件已保存 ---")
    simulation_app.close()