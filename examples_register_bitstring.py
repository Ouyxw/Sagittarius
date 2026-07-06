"""
Register Visualization with Bitstring Overlay Demo
===================================================

 plot_register() 的 bitstring 参数在寄存器图上可视化量子态分布。
"""

import matplotlib.pyplot as plt
from sagittarius import Register, Atom, Simulation, PulseSequence, SolverConfig
from sagittarius.viz import plot_register

print("=" * 80)
print("📊 寄存器可视化 - 比特串叠加功能演示")
print("=" * 80)

# ==============================================================================
# 1. 创建测试寄存器
# ==============================================================================
reg = Register.chain(5, spacing=5.0, blockade_radius=8.0)
print(f"\n✅ 创建了 5 原子链寄存器，阻塞半径: 8.0 μm")

# ==============================================================================
# 2. 基础用法：叠加比特串
# ==============================================================================
print("\n🔹 示例 1: 基础比特串叠加")
print("   比特串: 10101 (交替模式)")

fig, ax = plt.subplots(figsize=(10, 4))
plot_register(
    reg,
    bitstring="10101",
    ax=ax,
    title="Alternating Pattern: 10101"
)
plt.tight_layout()
plt.savefig("/tmp/demo_bitstring_basic.png", dpi=150, bbox_inches='tight')
plt.close()
print("   ✅ 图片已保存至 /tmp/demo_bitstring_basic.png")
print("   📝 橙色 = 激发态 (1), 蓝色 = 基态 (0)")

# ==============================================================================
# 3. 自定义颜色
# ==============================================================================
print("\n🔹 示例 2: 自定义颜色")
print("   比特串: 11000 (前两个原子激发)")

fig, ax = plt.subplots(figsize=(10, 4))
plot_register(
    reg,
    bitstring="11000",
    excited_state_color='red',
    ground_state_color='lightgray',
    ax=ax,
    title="Custom Colors: Red Excited, Gray Ground"
)
plt.tight_layout()
plt.savefig("/tmp/demo_bitstring_colors.png", dpi=150, bbox_inches='tight')
plt.close()
print("   ✅ 图片已保存至 /tmp/demo_bitstring_colors.png")

# ==============================================================================
# 4. 结合阻塞圆盘和边
# ==============================================================================
print("\n🔹 示例 3: 结合阻塞圆盘和边")
print("   比特串: 01010")

fig, ax = plt.subplots(figsize=(10, 4))
plot_register(
    reg,
    bitstring="01010",
    blockade_radius=8.0,
    show_blockade_disks=True,
    disk_alpha=0.15,
    edges=True,
    ax=ax,
    title="Bitstring + Blockade Disks + Edges"
)
plt.tight_layout()
plt.savefig("/tmp/demo_bitstring_combined.png", dpi=150, bbox_inches='tight')
plt.close()
print("   ✅ 图片已保存至 /tmp/demo_bitstring_combined.png")
print("   📋 显示: 比特串 + 阻塞圆盘 + 阻塞关联边")

# ==============================================================================
# 5. 从仿真结果提取最概然比特串
# ==============================================================================
print("\n🔹 示例 4: 从仿真结果提取最概然比特串")

pulse = PulseSequence(omega=2.0, delta=0.0, duration=3.0)
sim = Simulation(reg, pulse, SolverConfig(saveat=[3.0]))
result = sim.run()

dist = result.final_bitstring_distribution()
print(f"   比特串分布: {dist}")

if dist:
    top_bitstring = max(dist, key=dist.get)
    top_prob = dist[top_bitstring]
    
    print(f"   最概然比特串: {top_bitstring} (概率: {top_prob:.4f})")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    plot_register(
        reg,
        bitstring=top_bitstring,
        blockade_radius=8.0,
        edges=True,
        ax=ax,
        title=f"Most Probable State: {top_bitstring} (p={top_prob:.3f})"
    )
    plt.tight_layout()
    plt.savefig("/tmp/demo_bitstring_simulation.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("   ✅ 图片已保存至 /tmp/demo_bitstring_simulation.png")
else:
    print("   ⚠️  未获取到比特串分布")

# ==============================================================================
# 6. MWIS 问题求解可视化
# ==============================================================================
print("\n🔹 示例 5: MWIS 问题求解可视化")

mwis_solution = "10101"
weights = [1, 2, 3, 2, 1]
total_weight = sum(w for w, b in zip(weights, mwis_solution) if b == '1')

print(f"   MWIS 解: {mwis_solution}")
print(f"   选中原子: {[i for i, b in enumerate(mwis_solution) if b == '1']}")
print(f"   总权重: {total_weight}")

fig, ax = plt.subplots(figsize=(10, 4))
plot_register(
    reg,
    bitstring=mwis_solution,
    blockade_radius=8.0,
    edges=True,
    excited_state_color='gold',
    ground_state_color='silver',
    ax=ax,
    title=f"MWIS Solution: {mwis_solution} (Weight: {total_weight})"
)
plt.tight_layout()
plt.savefig("/tmp/demo_bitstring_mwis.png", dpi=150, bbox_inches='tight')
plt.close()
print("   ✅ 图片已保存至 /tmp/demo_bitstring_mwis.png")

# ==============================================================================
# 7. 多比特串对比
# ==============================================================================
print("\n🔹 示例 6: 单激发态对比")

bitstrings = ["10000", "01000", "00100", "00010", "00001"]
fig, axes = plt.subplots(1, 5, figsize=(20, 4))

for ax, bs in zip(axes, bitstrings):
    plot_register(reg, bitstring=bs, ax=ax, title=f"{bs}")
    ax.set_xlabel("")
    ax.set_ylabel("")

plt.suptitle("Single Excitation States", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("/tmp/demo_bitstring_comparison.png", dpi=150, bbox_inches='tight')
plt.close()
print("   ✅ 图片已保存至 /tmp/demo_bitstring_comparison.png")

# ==============================================================================
# 总结
# ==============================================================================
print("\n" + "=" * 80)
print("💡 使用建议:")
print("=" * 80)
print("1. 基础用法:")
print("   ax = plot_register(register, bitstring='01010')")
print("")
print("2. 自定义颜色:")
print("   ax = plot_register(register, bitstring='11000',")
print("                      excited_state_color='red',")
print("                      ground_state_color='blue')")
print("")
print("3. 结合其他功能:")
print("   ax = plot_register(register, bitstring='10101',")
print("                      blockade_radius=8.0,")
print("                      show_blockade_disks=True,")
print("                      edges=True)")
print("")
print("4. 从仿真结果自动提取:")
print("   dist = result.final_bitstring_distribution()")
print("   top_bs = max(dist, key=dist.get)")
print("   ax = plot_register(register, bitstring=top_bs)")
print("")
print("5. 错误处理:")
print("   - 比特串长度必须与原子数匹配")
print("   - 只能包含 '0' 和 '1' 字符")
print("=" * 80)

print("\n✅ 所有演示完成！")
