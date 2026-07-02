from sagittarius import Register

chain = Register.chain(3, spacing=0.5, C6=100.0)
lattice = Register.square_lattice(2, 2, spacing=1.0)
udg = Register.udg([(0.0, 0.0), (0.5, 0.0), (2.0, 0.0)], blockade_radius=1.0)

print(chain.topology["kind"])
print(len(lattice.atoms))
print(udg.geometry_summary(blockade_radius=1.0)["blockade_edge_count"])