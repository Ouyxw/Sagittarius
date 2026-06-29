# Observables in Neutral-Atom Simulations

Observables are quantities read out from the simulated quantum state during or after time evolution. The Hamiltonian determines how the state evolves; observables determine what physical information is extracted from that state.

Sagittarius currently exposes `RydbergPopulation` as the built-in Julia observable and the Python shorthand `observables={"name": atom_index}` for single-atom Rydberg populations. The observable library planned in `REQUIREMENTS.md` extends this into a stable set of neutral-atom and optimization diagnostics. This page defines the physical meaning of those observables.

## State and basis convention

The computational basis is represented by integer bitstrings. Bit `i` indicates whether atom `i` is in the Rydberg state, with Julia APIs using one-based atom indices and Python APIs using zero-based atom indices at the SDK boundary.

For an atom `i`, Sagittarius uses

\[
n_i = |r_i\rangle\langle r_i|
\]

as the Rydberg occupation operator. Its expectation value is the probability that atom `i` is in the Rydberg state.

For a wavefunction `psi`, diagonal observables are computed from probabilities `abs2(psi[k])`. For a density matrix `rho`, they are computed from diagonal entries `real(rho[k,k])`. In a reduced basis, the observable must interpret state components using the same `BasisContext` as the Hamiltonian and jump operators.

## Single-atom Rydberg population

\[
\langle n_i \rangle
\]

This is the probability that atom `i` is in the Rydberg state. It is the most direct diagnostic for blockade dynamics, local excitation transfer, pulse calibration, and final-state readout.

In a two-level neutral-atom qubit model, this can also be interpreted as the probability of measuring the atom in the state identified with `|r>`, subject to the chosen encoding.

Typical uses:

- verify Rabi oscillations on one or more atoms;
- inspect whether a pulse transfers population into selected sites;
- compare CPU, GPU, Lindblad, and MCWF trajectories through a compact scalar signal;
- expose Python result columns such as `pop0`, `atom1`, or `center`.

## Total Rydberg population

\[
N_r = \sum_i \langle n_i \rangle
\]

This is the expected number of Rydberg excitations in the register. It summarizes how strongly the system is excited without specifying where those excitations are located.

Typical uses:

- monitor excitation buildup during adiabatic or annealing protocols;
- detect whether blockade is suppressing multiple excitations;
- compare protocols with different drive strengths or detuning schedules;
- sanity-check that the simulation remains in a physically expected excitation sector.

## Pair correlation

\[
\langle n_i n_j \rangle
\]

This is the probability that atoms `i` and `j` are both in the Rydberg state at the same time. In Rydberg blockade systems, nearby atoms should have strongly suppressed pair correlation.

Typical uses:

- verify blockade suppression for close atom pairs;
- measure spatial excitation correlations;
- evaluate graph constraints in UDG or MWIS mappings;
- identify unwanted double excitations.

## Connected pair correlation

\[
C_{ij} = \langle n_i n_j \rangle - \langle n_i \rangle\langle n_j \rangle
\]

This removes the part of the pair signal expected from independent occupations. Positive values indicate that two atoms are excited together more often than expected from their single-site populations. Negative values indicate anticorrelation, which is common for nearby blocked pairs.

Typical uses:

- distinguish genuine correlations from large single-site populations;
- diagnose blockade-induced anticorrelation;
- study ordering or clustering tendencies in many-body dynamics.

## Blockade violation

For a set of constrained edges `E`,

\[
V_\mathrm{viol} = \sum_{(i,j)\in E}\langle n_i n_j \rangle.
\]

This is the expected number of violated blockade or graph constraints. In an ideal independent-set interpretation, adjacent vertices must not both be selected, so this quantity should be near zero.

Typical uses:

- evaluate whether a final state satisfies a UDG or MWIS constraint;
- compare graph-construction radius with `blockade_radius`;
- quantify leakage into physically or combinatorially invalid states;
- separate objective quality from feasibility.

A low violation value does not by itself imply an optimal solution; it only indicates that constrained pairs are rarely co-excited.

## Bitstring probability

For a target bitstring `b`,

\[
P(b) = |\langle b | \psi \rangle|^2
\]

for a wavefunction, or

\[
P(b) = \rho_{bb}
\]

for a density matrix.

This is the probability of measuring a specific final configuration. In optimization workflows, a bitstring usually corresponds to a candidate solution. In a reduced basis, forbidden bitstrings have probability zero because they are not represented in the state vector.

Typical uses:

- track success probability for a known target state;
- compare final-state distributions across protocols;
- inspect whether an annealing schedule concentrates probability on valid or optimal solutions;
- debug basis ordering and readout conventions.

## Cost or MWIS expectation

For a weighted independent-set style objective, a common diagnostic is

\[
C = \sum_i w_i\langle n_i \rangle - \lambda\sum_{(i,j)\in E}\langle n_i n_j \rangle.
\]

The first term rewards selected vertices. The second term penalizes constraint violations. The sign and penalty convention should match the problem formulation being analyzed.

Typical uses:

- estimate expected objective value during AQC or annealing;
- compare schedules without sampling every final bitstring;
- separate reward accumulation from constraint violation;
- validate MWIS demonstrations against exact classical baselines.

For reporting optimization performance, this expectation should be paired with final bitstring statistics, feasibility rate, and exact-solver comparisons where available.

## Pauli-Z and Pauli-ZZ

If the two-level atom is interpreted as a qubit, a Pauli-Z observable can be derived from the Rydberg occupation. The sign depends on the encoding convention. A common convention is

\[
Z_i = 1 - 2n_i,
\]

where the ground state has `Z=+1` and the Rydberg state has `Z=-1`. The opposite convention is also possible, so documentation and metadata must state which one is used.

Two-body Pauli-ZZ observables measure correlated qubit readout:

\[
Z_i Z_j.
\]

Typical uses:

- compare neutral-atom dynamics with spin-model notation;
- compute magnetization and spin correlations;
- analyze stabilizer-like or parity-sensitive outputs;
- translate between Rydberg occupation and qubit measurement conventions.

## Parity

For a set of atoms `S`, parity measures whether the number of selected or excited atoms in that set is even or odd. With the convention `Z_i = 1 - 2n_i`, parity is

\[
\Pi_S = \prod_{i\in S} Z_i.
\]

Typical uses:

- diagnose correlated readout patterns;
- measure stabilizer-like quantities;
- compactly summarize multi-atom bitstring structure;
- compare simulated readout with parity-based experimental analyses.

The physical interpretation depends on whether parity is defined over Rydberg excitations, qubit `1` states, or a signed Pauli-Z convention.

## Survival probability and fidelity

For an initial or target pure state `phi`, the overlap diagnostic is

\[
F_\phi(t) = |\langle \phi | \psi(t) \rangle|^2.
\]

For density matrices,

\[
F_\phi(t) = \langle \phi | \rho(t) | \phi \rangle.
\]

When `phi` is the initial state, this is often called survival probability or return probability. When `phi` is a desired final state, it is a target-state fidelity.

Typical uses:

- verify small-system protocols with known target states;
- quantify return probability after a quench;
- compare adiabatic schedules against an expected ground state;
- validate solver behavior against analytic or exact-reference dynamics.

## Energy expectation

For a Hamiltonian `H(t)`,

\[
E(t) = \langle \psi(t) | H(t) | \psi(t) \rangle
\]

or, for a density matrix,

\[
E(t) = \mathrm{Tr}[\rho(t)H(t)].
\]

This measures the instantaneous energy in the modeled rotating-frame Hamiltonian. Because Sagittarius uses a sign convention with detuning term `-Delta_i n_i`, energy values should be interpreted with that Hamiltonian convention.

Typical uses:

- monitor adiabatic following;
- compare final states against cost Hamiltonians;
- diagnose nonadiabatic excitations;
- check energy conservation in time-independent closed-system simulations.

Energy can include off-diagonal drive terms, so it is more sensitive to basis mapping and state type than purely diagonal occupation observables.

## Observable selection guidance

Use single-site populations for quick pulse and readout diagnostics. Use pair correlations and blockade violation when constraints matter. Use bitstring probabilities and cost expectations for optimization workflows. Use Pauli-Z, Pauli-ZZ, and parity when comparing against qubit or spin-model language. Use fidelity or energy when a reference state or Hamiltonian-level diagnostic is available.

For reduced-basis simulations, prefer observables that share an explicit `BasisContext` with the Hamiltonian. For publishable performance or physics claims, report enough metadata to reproduce the observable definition: atom indexing convention, basis mode, edge list, weights, penalties, target bitstrings, and sign conventions.
