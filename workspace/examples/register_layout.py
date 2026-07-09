import os
import matplotlib
matplotlib.use("Agg")  # 使用非交互式后端，不弹出窗口
from pathlib import Path
import matplotlib.pyplot as plt

from sagittarius import Register
from sagittarius.viz import plot_register

# 创建一个包含 6 个原子的线性 Register
reg = Register.chain(
    6,
    spacing=5.0,
    C6=80.0,  # C6 系数（用于计算阻塞半径）
)

# 绘制 Register
ax = plot_register(
    register=reg,
    blockade_radius=8.0,  # 在绘图时指定阻塞半径
    edges=True,
    labels=True,
    show_blockade_disks=True,
    bitstring="010101",
    title="Example Register Layout",
)

# 当前脚本所在目录
script_dir = Path(__file__).parent

# output 文件夹
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "register_layout.png"
ax.figure.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
)

# 释放资源
plt.close(ax.figure)

print(f"Figure saved to {output_file}")