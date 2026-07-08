from sagittarius import Register, Atom
from sagittarius.viz import generate_basis_diagnostics

# 创建3原子寄存器（与test_viz_basis_diagnostics中的small_register_3atoms相同）
atoms = [
    Atom(0.0, 0.0, 0.0),
    Atom(0.5, 0.0, 0.0),
    Atom(2.0, 0.0, 0.0),
]
reg = Register(atoms=atoms)

# 生成诊断数据
diag = generate_basis_diagnostics(reg, blockade_radius=1.0)

# 完整打印
print("=== Basis Diagnostics Raw Data ===")
for k, v in diag.items():
    print(f"{k:22s}: {v}")
