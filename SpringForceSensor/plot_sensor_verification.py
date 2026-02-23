import pandas as pd
import matplotlib.pyplot as plt

# ===== Read CSV from same directory =====
df = pd.read_csv("./Data_recording.csv")   # replace with your filename

# ===== Compute theoretical fz and error rate =====
g = 9.81
df["fz_theory"] = -g * df["m"]
df["err_rate"] = abs(df["fz"] - df["fz_theory"]) * 100 * (-1) / df["fz_theory"]

# ===== Plot =====
fig, ax1 = plt.subplots(figsize=(7, 4))

l1, = ax1.plot(df["m"], df["fz"], marker="o", linewidth=1.5, label="Measured $f_z$")
l2, = ax1.plot(df["m"], df["fz_theory"], marker="s", linewidth=1.5, label=r"Theory $f_z=-9.81 * \,mass$")

ax1.set_xlabel("Mass $m$ (kg)")
ax1.set_ylabel("Force $f_z$ (N)")
ax1.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

ax2 = ax1.twinx()
l3, = ax2.plot(df["m"], df["err_rate"], marker="^", linewidth=1.5, label="Absolute error rate")
ax2.set_ylabel("Absolute error rate %")

lines = [l1, l2, l3]
labels = [ln.get_label() for ln in lines]
ax1.legend(lines, labels, loc="best")

plt.tight_layout()
plt.show()
