from isaacsim import SimulationApp
import os
import numpy as np
import csv
from PIL import Image

simulation_app = SimulationApp({"headless": False})

from isaacsim.core.api import World
import isaacsim.core.utils.prims as prim_utils
from isaacsim.sensors.camera import Camera
from pxr import Gf, UsdLux

# Place objects parameter
sphere_radius = 0.1
cube_scale = [0.05, 0.05, 0.1]
cube_translation = [0.12, -0.12, 0.1]

# Recording parameter
focal_length = 2
NUM_FRAMES = 10
RADIUS = 0.4 
HEIGHT = 0.4
BASELINE = 0.06
TARGET_POINT = np.array([0.0, 0.0, 0.0])

# Output dir
output_dir = os.path.abspath("./stereo_parallel_recording_4")


# Orientation calculation: -Z of lookAt in Isaac Sim 's convention, towards +X in usd's convention.
def get_rig_orientation(eye_pos, target_pos):
    eye = Gf.Vec3d(*eye_pos.tolist())
    target = Gf.Vec3d(*target_pos.tolist())
    up = Gf.Vec3d(0, 0, 1)
    
    lookat_m = Gf.Matrix4d().SetLookAt(eye, target, up)
    cam_matrix = lookat_m.GetInverse()
    
    # Combined rotation:
    # 1. Rotate 90 degrees around Y-axis to make +X point at the target
    # 2. Rotate -90 degrees around its own X-axis to compensate for image roll, making the view upright
    combined_rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90) * Gf.Rotation(Gf.Vec3d(0, 1, 0), 90)
    correction = Gf.Matrix4d().SetRotate(combined_rot)
    
    final_matrix = correction * cam_matrix
    q = final_matrix.ExtractRotationQuat()
    return np.array([q.GetReal(), *q.GetImaginary()])

# 2. Initialize paths and folders
left_dir = os.path.join(output_dir, "left")
right_dir = os.path.join(output_dir, "right")
os.makedirs(left_dir, exist_ok=True)
os.makedirs(right_dir, exist_ok=True)

my_world = World(stage_units_in_meters=1.0)
my_world.scene.add_default_ground_plane()

# 3. Scene setup
stage = prim_utils.get_current_stage()
UsdLux.DomeLight.Define(stage, "/World/DomeLight").CreateIntensityAttr(1200.0)
UsdLux.DistantLight.Define(stage, "/World/DistantLight").CreateIntensityAttr(2000.0)

prim_utils.create_prim("/World/obj_sphere", "Sphere", translation=(0.0, 0.0, sphere_radius), attributes={"radius": sphere_radius})
prim_utils.create_prim("/World/obj_cube", "Cube", translation=(cube_translation[0], cube_translation[1], cube_translation[2]), scale=(cube_scale[0], cube_scale[1], cube_scale[2]))

my_world.reset()

# 4. Initialize cameras and save intrinsic parameters
cam_l = Camera(prim_path="/World/cam_l", resolution=(1280, 720))
cam_r = Camera(prim_path="/World/cam_r", resolution=(1280, 720))
cam_l.initialize()
cam_r.initialize()
cam_l.set_focal_length(focal_length) # f = 20mm
cam_r.set_focal_length(focal_length) # f = 20mm
cam_l.set_clipping_range(near_distance=0.01, far_distance=10000.0)
cam_r.set_clipping_range(near_distance=0.01, far_distance=10000.0)

# Get and save intrinsics file
intrinsic_l = cam_l.get_intrinsics_matrix()
intrinsic_r = cam_r.get_intrinsics_matrix()


with open(os.path.join(output_dir, "camera_parameters.txt"), "w") as f:
    f.write("Stereo Camera Intrinsics in pixel\n")
    f.write("========================\n\n")
    f.write(f"Left Camera Intrinsics:\n{intrinsic_l}\n\n")
    f.write(f"Right Camera Intrinsics:\n{intrinsic_r}\n\n")
    f.write(f"**** replace both the focal length with {focal_length * 10} in the unit of mm. ****\n")
    f.write("========================\n\n")
    f.write(f"sphere with radius of {sphere_radius} meter is placed on the origin.\n")
    f.write(f"cube in size of {[i * 2 for i in cube_scale]}(meter) is placed at {cube_translation}\n")
    f.write(f"camera is in a orbit with the radius = {RADIUS} meter and height = {HEIGHT} meter, pointing at the origin.\n")
    f.write(f"baseline = {BASELINE} meter.\n")
    f.write("=========== Eazy Copy =============\n\n")
    im_in_list = [[j for j in i] for i in intrinsic_l]

# 5. Prepare CSV file
csv_path = os.path.join(output_dir, "camera_poses.csv")
csv_file = open(csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
# Header: frame, sim_time, left_pos(x,y,z), left_quat(w,x,y,z), right_pos, right_quat
csv_writer.writerow(["frame", "time", "pos_l_x", "pos_l_y", "pos_l_z", "quat_l_w", "quat_l_x", "quat_l_y", "quat_l_z",
                     "pos_r_x", "pos_r_y", "pos_r_z", "quat_r_w", "quat_r_x", "quat_r_y", "quat_r_z"])


print(">>> Preheating renderer...")
for _ in range(30):
    my_world.step(render=True)

try:
    for i in range(NUM_FRAMES):
        # 1. Calculate trajectory position
        angle_rad = np.radians((i / NUM_FRAMES) * 360)
        center_pos = np.array([RADIUS * np.cos(angle_rad), RADIUS * np.sin(angle_rad), HEIGHT])
        
        # 2. Calculate corrected orientation
        rig_quat = get_rig_orientation(center_pos, TARGET_POINT)
        
        # 3. Calculate left/right camera positions (parallel axis configuration)
        view_dir_h = np.array([center_pos[0], center_pos[1], 0]) / RADIUS
        side_vec = np.array([-view_dir_h[1], view_dir_h[0], 0]) 
        
        pos_l = center_pos + side_vec * (BASELINE / 2.0)
        pos_r = center_pos - side_vec * (BASELINE / 2.0)
        
        # 4. Set pose
        cam_l.set_world_pose(position=pos_l, orientation=rig_quat)
        cam_r.set_world_pose(position=pos_r, orientation=rig_quat)
        
        # Render and update
        my_world.step(render=True)
        simulation_app.update()
        curr_sim_time = my_world.current_time
        
        # 5. Capture and save images
        img_l = cam_l.get_rgba()
        img_r = cam_r.get_rgba()
        
        if img_l is not None and img_l.size > 0:
            # Images are already upright due to rig orientation, save directly
            Image.fromarray(img_l[:, :, :3].astype(np.uint8)).save(os.path.join(left_dir, f"{i:04d}.png"))
            Image.fromarray(img_r[:, :, :3].astype(np.uint8)).save(os.path.join(right_dir, f"{i:04d}.png"))
            
            # 6. Record pose data to CSV
            csv_writer.writerow([
                i, curr_sim_time,
                pos_l[0], pos_l[1], pos_l[2], rig_quat[0], rig_quat[1], rig_quat[2], rig_quat[3],
                pos_r[0], pos_r[1], pos_r[2], rig_quat[0], rig_quat[1], rig_quat[2], rig_quat[3]
            ])
            
        if i % 20 == 0:
            print(f"Schedule: {i}/{NUM_FRAMES} | Time: {curr_sim_time:.2f}s")

except Exception as e:
    print(f"Error occurred: {e}")
finally:
    csv_file.close()
    print(f">>> Task completed.")
    print(f"Images saved to: {left_dir} & {right_dir}")
    print(f"Pose data saved to: {csv_path}")
    print(f"Camera parameters saved to: {os.path.join(output_dir, 'camera_parameters.txt')}")
    simulation_app.close()