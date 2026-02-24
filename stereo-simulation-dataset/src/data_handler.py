import os
import csv
import numpy as np
from PIL import Image
import shutil

class DatasetWriter:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.left_dir = os.path.join(output_dir, "left")
        self.right_dir = os.path.join(output_dir, "right")

        # --- 新增：清空逻辑 ---
        if os.path.exists(self.output_dir):
            print(f">>> Detected existing output directory: {self.output_dir}. Cleaning up...")
            # 这种方式会删除整个文件夹及其内容
            shutil.rmtree(self.output_dir)
        
        os.makedirs(self.left_dir, exist_ok=True)
        os.makedirs(self.right_dir, exist_ok=True)
        
        self.csv_path = os.path.join(output_dir, "camera_poses.csv")
        self.csv_file = open(self.csv_path, 'w', newline='')
        self.writer = csv.writer(self.csv_file)
        
        self.writer.writerow([
            "frame", "time", 
            "p_l_x", "p_l_y", "p_l_z", "q_w", "q_x", "q_y", "q_z",
            "p_r_x", "p_r_y", "p_r_z"
        ])

    def save_metadata(self, config, intrinsic_matrix):
        """
        保存数据集描述和相机内参
        intrinsic_matrix: 3x3 的 numpy 数组
        """
        meta_path = os.path.join(self.output_dir, "dataset_info.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("=== Synthetic Stereo Dataset Metadata ===\n")
            f.write(f"Scene Mode: {config.SCENE_MODE}\n")
            f.write(f"Orbit Mode: {config.ORBIT_MODE}\n")
            f.write(f"Resolution: {config.RESOLUTION[0]}x{config.RESOLUTION[1]}\n")
            f.write(f"Focal Length: {10 * config.FOCAL_LENGTH}mm\n")
            f.write(f"Stereo Baseline: {config.BASELINE}m\n")
            f.write("-" * 40 + "\n")
            f.write("Camera Intrinsic Matrix (K):\n")
            f.write(np.array2string(intrinsic_matrix, separator=', '))
            f.write("\n\n" + "-" * 40 + "\n")
            f.write("Scene Details:\n")
            if config.SCENE_MODE == "diy":
                f.write(f" - Sphere Radius: {config.SPHERE_RADIUS}m\n")
                f.write(f" - Cube Scale: {config.CUBE_SCALE}m\n")
            else:
                f.write(f" - Imported USD: {config.USD_PATH}\n")
        # --- 新增：特定格式化输出 (Easy Copy 格式) ---
            f.write("=== Easy Copy Format (K_flat and Baseline) ===\n")
            
            # 1. 将 3x3 矩阵展平为包含 9 个元素的列表
            k_flat = intrinsic_matrix.flatten()
            
            # 2. 格式化为：空格分隔的字符串 (使用 :g 自动处理有效数字，避免过长的 0)
            k_line = " ".join([f"{x:1}" for x in k_flat])
            
            # 3. 写入文件
            f.write(k_line + "\n")
            f.write(f"{config.BASELINE}\n")
        print(f">>> Metadata and Intrinsics saved to: {meta_path}")

    def write_frame(self, frame_id, time, pos_l, pos_r, quat, img_l, img_r):
        file_name = f"{frame_id:04d}.png"
        
        img_l_pix = Image.fromarray(img_l[:, :, :3].astype(np.uint8))
        img_r_pix = Image.fromarray(img_r[:, :, :3].astype(np.uint8))
        
        img_l_pix.save(os.path.join(self.left_dir, file_name))
        img_r_pix.save(os.path.join(self.right_dir, file_name))
        
        self.writer.writerow([
            frame_id, f"{time:.4f}",
            pos_l[0], pos_l[1], pos_l[2], 
            quat[0], quat[1], quat[2], quat[3],
            pos_r[0], pos_r[1], pos_r[2]
        ])

    def close(self):
        if hasattr(self, 'csv_file'):
            self.csv_file.close()
            print(">>> CSV file closed.")