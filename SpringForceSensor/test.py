# create the sensor
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
from pxr import Gf, UsdLux

# 2. 初始化世界
world = World(stage_units_in_meters=1.0)
stage = omni.usd.get_context().get_stage()
UsdLux.DomeLight.Define(stage, "/World/DomeLight").CreateIntensityAttr(1200.0)
UsdLux.DistantLight.Define(stage, "/World/DistantLight").CreateIntensityAttr(2000.0)

scene = world.get_physics_context()
scene.enable_gpu_dynamics(True)
# scene.set_solver_position_iteration_count(64) # 针对高精度变形强制增加 # invalid
scene.set_broadphase_type("GPU")

world.scene.add_default_ground_plane()
sensor = SpringForceSensor("/World/Sensor")

world.reset()

try:
    i = 0
    while simulation_app.is_running():
        world.step(render=True)
        i += 1
        if i%100 == 0:
            print(f"watchdog output: {i}")

except Exception as e:
    print(f"错误: {e}")
finally:
    print("Done")
    simulation_app.close()