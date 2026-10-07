---
name: matlab-numerics
description: MATLAB numerical modeling and scientific computing for university and graduate work - ODEs (ode45/ode15s, stiffness, events, BVPs, DDEs), root finding, linear systems, interpolation, numerical integration/differentiation, error and convergence analysis, PDEs by finite differences, method of lines and pdepe, and model fitting/parameter estimation. Use whenever the user asks to solve, simulate, model or fit something in MATLAB or Octave, debugs a .m file with a numerical problem, or has a numerical-methods assignment, even if MATLAB is only implied.
---

# MATLAB numerical modeling

Students and researchers come here with a model (a physical system, an equation, a dataset) and
need MATLAB code that is **correct, verified, and explained**. A plot that looks plausible is not
evidence of correctness; the core habit of this skill is to always show *why* the numbers can be
trusted (a known solution, a convergence study, a conservation law, or a tolerance check).

All code, comments, labels and explanations are in English.

## Workflow

1. **Formulate.** Write the mathematical problem explicitly before coding: unknowns, equations,
   domain, initial/boundary conditions, parameter values with units. For ODEs reduce to a
   first-order system `y' = f(t, y)` and state what each component of `y` is. Nondimensionalize
   when scales differ by many orders of magnitude.
2. **Choose the method** with a one-line justification (see the table below and the references).
   If the assignment prescribes a method (e.g. "use RK4 with h = 0.1"), implement exactly that,
   then optionally compare with a built-in solver.
3. **Implement** following the conventions below.
4. **Verify** at least one way (see Verification). Report the evidence, not just "it works".
5. **Present**: results (table/figure), what they mean physically, limitations.

### Which reference to read

| Problem | Read |
|---|---|
| ODE initial value problems, stiffness, events, DAEs, BVPs (`bvp4c`), delays (`dde23`) | `references/ode.md` |
| Roots, nonlinear systems, linear systems, interpolation, integration, differentiation, error/convergence | `references/numerical-methods.md` |
| Heat/wave/Laplace/advection equations, finite differences, stability (CFL), method of lines, `pdepe` | `references/pde.md` |
| Curve fitting, parameter estimation (incl. ODE models), optimization, uncertainty | `references/modeling-fitting.md` |

Helpers in `scripts/` (copy them next to the user's code when used): `rk4.m` (fixed-step RK4 for
systems), `conv_order.m` (observed order of convergence from errors or from successive
refinements), `fd_laplacian.m` (sparse 1D/2D finite-difference Laplacian with Dirichlet
boundaries). `assets/study_template.m` is a skeleton for a complete, verified study script.

## Coding conventions

- **Script layout:** parameters block → model functions → solve → verify → plot/report.
  Put local functions at the end of the script file (allowed since R2016b), or in separate files.
- **Pass parameters through anonymous functions** (`@(t,y) rhs(t,y,p)` with a struct `p`), never
  `global`. It keeps the model testable and parameter sweeps trivial.
- **Vectorize the RHS** and preallocate arrays (`zeros(n,1)`); avoid growing arrays in loops.
- **Set tolerances on purpose** for adaptive solvers (`odeset('RelTol',1e-6,'AbsTol',1e-9)`);
  defaults (`RelTol 1e-3`) are often too loose for reported results. `AbsTol` must reflect the
  scale of each component (it can be a vector).
- **Sparse matrices** for anything grid-based (`spdiags`, `kron`, `speye`); dense `n^2 x n^2`
  matrices are the most common reason student PDE codes crash or crawl.
- **Solve, don't invert:** `x = A\b`, never `inv(A)*b`. Check `cond(A)` when results look odd.
- **Plots must stand alone:** axis labels with units, legend, title, `grid on`, readable line
  widths; log scale (`loglog`, `semilogy`) for errors and convergence. Use distinct markers for
  numerical vs. exact/reference curves.
- **Reproducibility:** `rng(0)` before anything random; print key parameters with results.
- **Compatibility:** prefer functions in base MATLAB. Before using a toolbox function (e.g.
  `fsolve`, `lsqcurvefit`, `fmincon` from Optimization; `nlparci`, `fitnlm` from Statistics),
  either confirm the user has it or provide a base-MATLAB fallback (`fzero`/`fminsearch`/manual
  Newton). Note when code also runs in GNU Octave (most base code does; `ode45` and `fzero` do;
  `pdepe`, `bvp5c`, the R2023b `ode` object do not).

## Verification (pick what fits, more is better)

- **Exact solution** available or manufactured (method of manufactured solutions): plot the
  error, not just both curves.
- **Convergence study:** refine `h` / grid / tolerance and show the error decreases at the
  expected rate (`conv_order.m`). Expected: Euler 1, RK4 4, trapezoid 2, Simpson 4, central
  differences 2, FTCS O(dt, dx^2), Crank–Nicolson O(dt^2, dx^2).
- **Tolerance check** for adaptive solvers: rerun with tolerances 100× tighter; the reported
  quantities should not change at the digits you report.
- **Invariants:** conserved energy/mass/momentum, positivity, known steady state or equilibrium,
  symmetry.
- **Sanity limits:** parameter → 0 or → ∞ limits reproduce known simple behavior.
- **Residuals** for algebraic problems: report `norm(f(x))` / `norm(A*x-b)/norm(b)`.

## Explaining to students

When the user is learning (homework, exam prep, thesis chapter), after the code:
- state the method and its order/stability in one or two sentences,
- explain any choice that a grader would question (step size, tolerance, solver type),
- interpret the result physically,
- mention the main limitation or source of error.
Keep it proportional: short question → short answer with code; full assignment → structured
report (Problem, Method, Implementation, Verification, Results, Discussion).

## Common mistakes to catch in user code

- Using `ode45` on a stiff problem (very slow, millions of steps) → switch to `ode15s`/`ode23s`.
- `tspan = [0 10]` and then comparing outputs at "the same" times → pass a vector `tspan` or use
  `deval`, because adaptive solvers return their own time points.
- Row vs. column vectors: the ODE function must return a **column** vector.
- Explicit schemes run past their stability limit (FTCS with `r = alpha*dt/dx^2 > 1/2`, wave
  equation with Courant number `> 1`) → blow-up or oscillations that look like physics.
- Finite-difference step too small for derivatives (round-off dominates below ~`1e-8` for
  forward differences) → see the step-size trade-off in `numerical-methods.md`.
- `polyfit` with high degree on equispaced data (Runge phenomenon, ill-conditioning) → use
  splines or `polyfit` with centering/scaling (`[p,S,mu] = polyfit(...)`).
- Comparing floating-point numbers with `==`.
- Fitting parameters spanning orders of magnitude without scaling → fit `log` of parameters.
