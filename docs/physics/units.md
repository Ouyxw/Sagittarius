# Physical Units and Parameter Selection

Sagittarius does not attach units to numeric values. A simulation must therefore use one internally consistent unit system. The equations use \(\hbar=1\), so Hamiltonian coefficients are angular frequencies and time has the reciprocal unit.

A convenient experimental convention is:

- coordinates, lattice spacing, and `blockade_radius`: \(\mu\mathrm{m}\);
- `omega`, `delta`, and \(V_{ij}\): \(\mathrm{rad}/\mu\mathrm{s}\);
- `C6`: \((\mathrm{rad}/\mu\mathrm{s})\,\mu\mathrm{m}^6\);
- simulation times and pulse timing fields: \(\mu\mathrm{s}\);
- `gamma` and `gamma_phi`: \(\mu\mathrm{s}^{-1}\).

Other unit systems, including dimensionless units, are valid if every input is converted consistently. Values quoted as ordinary frequencies \(f\), such as MHz, must be converted to angular frequencies with \(\omega=2\pi f\) before being combined with the Hamiltonian.

## Hamiltonian convention

Sagittarius implements

\[
H(t)=\sum_i \frac{\Omega_i(t)}{2}\sigma_i^x
     -\sum_i \Delta_i(t)n_i
     +\sum_{i<j}\frac{C_6}{r_{ij}^6}n_i n_j.
\]

Here \(n_i=|r_i\rangle\langle r_i|\). Positive `delta` lowers the modeled Rydberg-state energy because the detuning term is \(-\Delta_i n_i\). The sign of `C6` determines whether the modeled van der Waals interaction is repulsive or attractive.

## Parameters and selection criteria

| Parameter | Physical meaning | Selection basis |
| :--- | :--- | :--- |
| Atom coordinates and `spacing` | Atom positions and pair separations \(r_{ij}\), which set both \(C_6/r_{ij}^6\) and the blockade graph. | Use one length unit throughout. Avoid coincident atoms, which make the interaction singular. Because of the sixth-power dependence, include position uncertainty in the interaction error budget. |
| `C6` | van der Waals coefficient in \(V_{ij}=C_6/r_{ij}^6\); its unit is angular-frequency times length to the sixth power. | Use the value and sign for the chosen species, Rydberg state, and field configuration, converted to the selected length and frequency units. |
| `omega` | Global or local Rabi angular frequency \(\Omega_i(t)\), controlling coherent \(|g\rangle\leftrightarrow|r\rangle\) transitions. | Use the calibrated drive envelope and hardware limits. For a resonant isolated atom under constant drive, the population period is \(2\pi/|\Omega|\); pulse area \(\int\Omega(t)dt\) is a useful check. |
| `delta` | Global or local detuning angular frequency \(\Delta_i(t)\); the implemented term is \(-\Delta_i n_i\). | Match the model's rotating-frame and sign convention. Choose sweeps relative to drive and interaction scales, and verify the sign with a small-system test. |
| Simulation time and pulse `duration`, `sigma`, `mu`, `width` | The common time coordinate used by the ODE and pulse functions. | Use the reciprocal unit of all Hamiltonian frequencies. Cover the complete schedule and resolve its shortest physical timescale. |
| `gamma` | Rydberg population-decay rate in \(\sqrt{\gamma}|g\rangle\langle r|\); without drive, population decays as \(e^{-\gamma t}\). | Set `gamma = 1/T1` in the simulation time unit, or provide per-atom rates. Use zero for closed-system evolution. |
| `gamma_phi` | Coefficient of the pure-dephasing jump operator \(\sqrt{\gamma_\phi}n\). With this implementation, isolated ground-Rydberg coherence decays at \(\gamma_\phi/2\). | For a desired pure-dephasing coherence time \(T_\phi\), use `gamma_phi = 2/T_phi`. With population decay, the modeled coherence rate is \(\gamma/2+\gamma_\phi/2\). |
| `blockade_radius` | Hard geometric cutoff that removes basis states containing two Rydberg excitations separated by less than the radius. `0.0` keeps the full basis. | Derive it from an explicit interaction threshold and validate the reduced basis against full-basis dynamics for a representative small system. |

`reltol`, `abstol`, solver `method`, GPU settings, and `n_trajectories` are numerical controls rather than physical parameters. Tighten tolerances and increase trajectory count until relevant observables are stable at the required precision.

## Choosing `blockade_radius`

The reduced basis excludes a pair when

\[
r_{ij}<R_b.
\]

Pairs exactly at `blockade_radius` are retained. The full \(C_6/r^6\) interaction remains active for all pairs represented in the reduced basis. Sagittarius does not calculate the radius from `C6`, `omega`, or `delta`; a radius stored as UDG topology metadata also does not enable basis reduction unless it is passed to `SolverConfig`.

Choose an interaction threshold \(E_\mathrm{cut}>0\) above which double excitation is treated as inaccessible, then estimate

\[
R_b=\left(\frac{|C_6|}{E_\mathrm{cut}}\right)^{1/6}.
\]

The threshold should exceed the largest competing scale over the complete protocol. A practical starting point is

\[
E_\mathrm{cut}=\kappa\max_t\left(\max_i|\Omega_i(t)|,\max_i|\Delta_i(t)|,1/T_\mathrm{protocol}\right),
\]

with a conservative \(\kappa>1\). There is no universal value: select it from the observable error budget or use the experiment's calibrated blockade criterion.

Before relying on a reduced-basis result:

1. Inspect all pairs satisfying \(r_{ij}<R_b\), especially those near the boundary.
2. Compare full- and reduced-basis dynamics on a representative small register while sweeping the radius or threshold.
3. Confirm target observables remain stable when the radius is modestly decreased. A larger radius improves pruning but makes a stronger physical approximation.
4. Re-evaluate the radius whenever geometry, `C6`, drive amplitude, detuning range, or protocol duration changes.

For UDG or MWIS studies, keep the graph-construction radius and `SolverConfig.blockade_radius` identical so that the optimization constraint and simulated Hilbert space agree.
