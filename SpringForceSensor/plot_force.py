import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

def main():
    # 1. 设置命令行参数解析
    parser = argparse.ArgumentParser(description="读取传感器力数据 CSV 并绘制 F_z 随时间变化的折线图")
    parser.add_argument("file_path", type=str, help="CSV 文件的路径")
    args = parser.parse_parse_args() if hasattr(parser, 'parse_parse_args') else parser.parse_args()

    # 2. 检查文件是否存在
    if not os.path.exists(args.file_path):
        print(f"错误: 找不到文件 '{args.file_path}'")
        return

    try:
        # 3. 读取 CSV 数据
        # 预期列名为: ['time', 'f_x', 'f_y', 'f_z', 'base_z']
        data = pd.read_csv(args.file_path)

        if 'time' not in data.columns or 'f_z' not in data.columns:
            print("错误: CSV 文件格式不正确，缺少 'time' 或 'f_z' 列。")
            return

        # 4. 绘图设置
        plt.figure(figsize=(10, 6))
        plt.plot(data['time'], data['f_z'], label='Vertical Force ($F_z$)', color='b', linewidth=1.5)

        # 5. 美化图表
        plt.title(f"Force Response Analysis\nSource: {os.path.basename(args.file_path)}", fontsize=14)
        plt.xlabel("Time (s)", fontsize=12)
        plt.ylabel("Force $F_z$ (N)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        # 标注开始产生压力的点（可选）
        # 找到第一个 F_z 显著偏离 0 的点
        threshold = 0.01 
        contact_points = data[abs(data['f_z']) > threshold]
        if not contact_points.empty:
            first_contact_t = contact_points['time'].iloc[0]
            first_contact_f = contact_points['f_z'].iloc[0]
            # plt.annotate('Contact Start', xy=(first_contact_t, first_contact_f), 
                        #  xytext=(first_contact_t + 0.5, first_contact_f + 5),
                        #  arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))

        # 6. 显示图表
        print(f"正在展示文件 {args.file_path} 的图表...")
        plt.show()

    except Exception as e:
        print(f"读取或绘图时出错: {e}")

if __name__ == "__main__":
    main()