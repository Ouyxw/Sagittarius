from sagittarius import Register, PulseSequence, dense_vs_reduced_validation

report = dense_vs_reduced_validation(
    Register.chain(3, spacing=0.5, C6=10.0),
    PulseSequence(omega=[0.2, 0.3, 0.4], delta=[-0.1, 0.0, 0.2]),
    blockade_radius=0.6,
    duration=0.7,
)

print(report["ok"])
print(report["basis"])
print(report["reduced_basis_pruning_ratio"])