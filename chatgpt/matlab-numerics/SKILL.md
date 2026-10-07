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
| ODE initial value problems, stiffness, events, DAEs, BVPs (`bvp4c`), delays (`dde23`) | Appendix A |
| Roots, nonlinear systems, linear systems, interpolation, integration, differentiation, error/convergence | Appendix B |
| Heat/wave/Laplace/advection equations, finite differences, stability (CFL), method of lines, `pdepe` | Appendix C |
| Curve fitting, parameter estimation (incl. ODE models), optimization, uncertainty | Appendix D |

Helpers in Appendix E (give the user these files when used): `rk4.m` (fixed-step RK4 for
systems), `conv_order.m` (observed order of convergence from errors or from successive
refinements), `fd_laplacian.m` (sparse 1D/2D finite-difference Laplacian with Dirichlet
boundaries). `study_template.m` (Appendix E) is a skeleton for a complete, verified study script.

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
  forward differences) → see the step-size trade-off in Appendix B.
- `polyfit` with high degree on equispaced data (Runge phenomenon, ill-conditioning) → use
  splines or `polyfit` with centering/scaling (`[p,S,mu] = polyfit(...)`).
- Comparing floating-point numbers with `==`.
- Fitting parameters spanning orders of magnitude without scaling → fit `log` of parameters.

---
# Appendices (reference material: read the relevant one when needed)

## Appendix A: ODEs in MATLAB

### Contents
1. Reducing to a first-order system
2. Choosing a solver
3. Standard solve pattern (tolerances, output, deval)
4. Stiffness: how to recognize it, what to do
5. Events (stop/record when something happens)
6. Mass matrices and DAEs
7. Boundary value problems (bvp4c)
8. Delay equations (dde23)
9. Hand-written methods for assignments (Euler, RK4, implicit)
10. Phase portraits, equilibria, linear stability
11. Parameter sweeps

### 1. Reducing to a first-order system

`m x'' + c x' + k x = F(t)` → `y = [x; v]`, `y' = [v; (F(t) - c v - k x)/m]`.
For an n-th order equation, introduce y1 = x, y2 = x', …, yn = x^(n-1). State the meaning of each
component in a comment.

```matlab
p = struct('m',1,'c',0.2,'k',4,'F0',1,'w',1.5);
rhs = @(t,y) [y(2); (p.F0*cos(p.w*t) - p.c*y(2) - p.k*y(1))/p.m];
```

### 2. Choosing a solver

| Solver | Type / order | Use when |
|---|---|---|
| `ode45` | explicit RK (4,5) | default for nonstiff problems, moderate accuracy |
| `ode23` | explicit RK (2,3) | crude tolerances, mildly stiff, or discontinuities |
| `ode78`, `ode89` (R2021b+) | high-order explicit RK | high accuracy on smooth nonstiff problems (orbits) |
| `ode113` | variable-order Adams–Bashforth–Moulton | stringent tolerances, expensive RHS |
| `ode15s` | variable-order NDF/BDF (1–5) | **stiff** problems, DAEs with mass matrix — first try for stiff |
| `ode23s` | Rosenbrock (2,3) | stiff with crude tolerances; constant mass matrix |
| `ode23t` | trapezoidal rule | moderately stiff, no numerical damping (oscillators), DAEs |
| `ode23tb` | TR-BDF2 | stiff, crude tolerances |
| `ode15i` | fully implicit | `f(t,y,y') = 0` |
| `dde23`, `ddesd` | delays | constant / state-dependent delays |
| `bvp4c`, `bvp5c` | collocation | boundary value problems |

R2023b+ also has the `ode` object (`F = ode(ODEFcn=@f, InitialValue=y0); S = solve(F,t0,tf)`)
which picks a solver automatically; use the classic functions unless the user is on that version
and prefers it (they're what courses and older code use).

### 3. Standard solve pattern

```matlab
y0    = [1; 0];
tspan = linspace(0, 20, 801);           % vector -> output exactly at these times
opts  = odeset('RelTol',1e-8,'AbsTol',1e-10);
[t, Y] = ode45(rhs, tspan, y0, opts);    % Y(:,1) = x, Y(:,2) = v

% or keep the continuous solution
sol = ode45(rhs, [0 20], y0, opts);
yq  = deval(sol, 7.3);                   % evaluate anywhere, consistent with solver accuracy
```

- `RelTol` controls relative error per step (default 1e-3); `AbsTol` (default 1e-6) matters when
  a component is near zero — set it below the smallest magnitude you care about, per component if
  scales differ (`'AbsTol',[1e-10 1e-6]`).
- Local error control ≠ global error. Verify by rerunning with tighter tolerances.
- `'MaxStep'` when the RHS has short features the solver could step over (pulses, forcing).
- Discontinuous forcing: integrate piecewise (restart at the discontinuity) instead of letting
  the solver struggle.
- Stats: `odeset('Stats','on')` prints steps / failed steps / function evaluations — useful
  evidence for stiffness discussions.

### 4. Stiffness

Signs: `ode45` takes a huge number of tiny steps although the solution is smooth; Jacobian
eigenvalues with very different magnitudes (`max|Re λ| / min|Re λ|` large) and negative real
parts; chemical kinetics, circuits, fast-slow systems, semi-discretized diffusion PDEs.

Do: switch to `ode15s` (or `ode23s`/`ode23tb`), supply the Jacobian (`'Jacobian',@J`) or at least
its sparsity pattern (`'JPattern',S`) for large systems — this is the biggest speedup for method
of lines. Show `Stats` of both solvers to demonstrate the difference.

Classic demo: Van der Pol with `mu = 1000`, Robertson chemical kinetics.

### 5. Events

```matlab
function [value, isterminal, direction] = hitGround(t, y)
    value      = y(1);   % event when height crosses zero
    isterminal = 1;      % stop integration
    direction  = -1;     % only when decreasing
end

opts = odeset('Events', @hitGround, 'RelTol',1e-8);
[t, Y, te, ye, ie] = ode45(rhs, [0 100], y0, opts);
```
For bouncing/impact: loop — integrate to the event, apply the jump (`v = -e*v`), restart from
`te` with the new state. Record `te` for periods (Poincaré sections, oscillation period).

### 6. Mass matrices and DAEs

`M(t,y) y' = f(t,y)` with singular `M` = semi-explicit DAE (index 1).
```matlab
opts = odeset('Mass', M, 'MassSingular','yes', 'RelTol',1e-6);
[t, Y] = ode15s(f, tspan, y0consistent, opts);
```
Initial conditions must be consistent with the algebraic equations (`decic` helps for `ode15i`).
Higher-index DAEs need index reduction first.

### 7. Boundary value problems

```matlab
% y'' + y = 0, y(0) = 0, y(pi/2) = 1  ->  y = [u; u']
odefun = @(x,y) [y(2); -y(1)];
bcfun  = @(ya,yb) [ya(1); yb(1) - 1];      % residuals: zero when BCs hold
solinit = bvpinit(linspace(0, pi/2, 10), [0 1]);   % mesh + constant guess
sol = bvp4c(odefun, bcfun, solinit, bvpset('RelTol',1e-6));
x = linspace(0, pi/2, 200); y = deval(sol, x);
```
- The initial guess matters for nonlinear BVPs; use a function handle guess or continuation
  (solve an easier problem, use its solution as the next guess).
- Unknown parameters (eigenvalues, periods): `bvpinit(x, yguess, pguess)`, `odefun(x,y,p)`,
  one extra boundary condition per parameter.
- Alternative for assignments: shooting method = `fzero` on the boundary mismatch of an IVP.

### 8. Delay equations

```matlab
lags = 1;                                   % y'(t) = -y(t-1)
ddefun = @(t,y,Z) -Z(:,1);                  % Z(:,j) = y(t - lags(j))
sol = dde23(ddefun, lags, @(t) 1, [0 10]);  % history function for t <= 0
```

### 9. Hand-written methods (when the assignment asks)

Use `rk4.m` (Appendix E) for fixed-step RK4 on systems. Explicit Euler in a few lines:
```matlab
N = round((tf-t0)/h); t = t0 + (0:N)*h; Y = zeros(numel(y0), N+1); Y(:,1) = y0;
for n = 1:N
    Y(:,n+1) = Y(:,n) + h*f(t(n), Y(:,n));
end
```
Implicit (backward) Euler for a stiff system: solve `y_{n+1} - y_n - h f(t_{n+1}, y_{n+1}) = 0`
each step with Newton (Jacobian `I - h J`) or, if linear `y' = A y`, `Y(:,n+1) = (I - h*A) \ Y(:,n)`
(factorize once with `decomposition` or `lu` when `h` is fixed).

Always pair hand-written methods with a convergence study (h, h/2, h/4, …) against a reference
(exact solution or `ode45` with `RelTol 1e-12`) and report the observed order via `conv_order.m`.
Stability: explicit Euler on `y' = λy` needs `|1 + hλ| ≤ 1`; RK4 region reaches about `-2.79` on
the real axis.

### 10. Phase portraits and stability

- Equilibria: solve `f(y) = 0` (`fzero` in 1D, `fsolve` or Newton in nD).
- Jacobian at equilibria (analytic or finite differences) → `eig(J)`: all `Re < 0` stable node/
  focus, mixed signs saddle, purely imaginary → center for the linearization (inconclusive).
- Direction field: `quiver` on a `meshgrid` of normalized `f`; overlay trajectories from several
  initial conditions; mark equilibria.

### 11. Parameter sweeps

Loop over parameter values with preallocated outputs; extract a scalar quantity per run (peak,
period, final value) and plot it against the parameter (bifurcation-style diagram). For many
runs use `parfor` only if the Parallel Toolbox is available.

## Appendix B: Core numerical methods in MATLAB

### Contents
1. Error, floating point, convergence order
2. Root finding (scalar) and nonlinear systems
3. Linear systems
4. Interpolation and approximation
5. Numerical integration
6. Numerical differentiation

### 1. Error, floating point, convergence

- `eps` ≈ 2.2e-16 (relative spacing at 1). Report relative error `abs(x - xref)/abs(xref)` when
  magnitudes vary.
- Order of convergence: if `e(h) ≈ C h^p`, then `p ≈ log(e1/e2)/log(h1/h2)`. Plot `loglog(h, e)`
  with a reference slope line. Without an exact solution use three refinements:
  `p ≈ log2(|u_h - u_{h/2}| / |u_{h/2} - u_{h/4}|)`. Both are in `conv_order.m`.
- Iterative methods: linear convergence `e_{k+1} ≈ C e_k`; quadratic (Newton) `e_{k+1} ≈ C e_k^2`.
  Show a table of `k, x_k, |f(x_k)|, |x_k - x_{k-1}|`.
- Richardson extrapolation: `(2^p u_{h/2} - u_h)/(2^p - 1)` improves accuracy by one order.
- Total error = truncation + round-off; there is an optimal step for differences (section 6).

### 2. Root finding

| Method | Needs | Convergence | MATLAB |
|---|---|---|---|
| Bisection | bracket, sign change | linear, guaranteed | write it (assignments) |
| Newton | `f'` | quadratic near simple root | write it |
| Secant | two starts | superlinear (≈1.618) | write it |
| Brent (bisection+secant+IQI) | bracket or start | robust, superlinear | `fzero(f, [a b])` |
| Polynomial roots | coefficients | eigenvalues of companion matrix | `roots(p)` |
| Systems | Jacobian (optional) | trust-region / Newton | `fsolve` (Optimization TB) |

```matlab
f = @(x) x.^3 - 2*x - 5;
x1 = fzero(f, [2 3]);                          % bracket = guaranteed
opts = optimset('TolX',1e-14,'Display','iter'); x2 = fzero(f, 2, opts);
```
Newton for systems without toolboxes:
```matlab
x = x0;
for k = 1:50
    F = Ffun(x); J = Jfun(x);
    dx = -J\F;  x = x + dx;
    if norm(dx) <= 1e-12*(1 + norm(x)), break, end
end
```
Pitfalls: multiple roots slow Newton to linear convergence; plot `f` first to find brackets;
stop on both step size and residual; guard against zero derivative.

### 3. Linear systems

- `x = A\b` picks the right algorithm (triangular, Cholesky for SPD, LU otherwise, QR for
  rectangular = least squares). Never `inv(A)*b`.
- Condition number: `cond(A)` (dense) or `condest(A)` (sparse). Expect to lose about
  `log10(cond(A))` digits. Report relative residual `norm(A*x-b)/norm(b)`.
- Reuse factorizations: `[L,U,P] = lu(A); x = U\(L\(P*b));` or `dA = decomposition(A); x = dA\b;`.
- Large sparse: `pcg` (SPD, with `ichol` preconditioner), `gmres`/`bicgstab` (nonsymmetric, with
  `ilu`). Always check the returned `flag` and `relres`.
- Classic iterations for courses (Jacobi, Gauss–Seidel, SOR): converge for strictly diagonally
  dominant or SPD matrices; spectral radius of the iteration matrix `max(abs(eig(T)))` < 1 is the
  criterion; optimal SOR ω for the model Poisson problem = `2/(1 + sin(pi*h))`.
- Eigenproblems: `eig` (dense), `eigs(A, k, 'smallestabs')` (sparse, few eigenvalues).
- Least squares / overdetermined: `A\b` (QR) or `lsqminnorm` for rank-deficient.

### 4. Interpolation and approximation

- `interp1(x, y, xq, method)`: `'linear'`, `'pchip'` (shape-preserving, no overshoot — good for
  physical monotone data), `'spline'` (smooth C2, may overshoot), `'makima'`.
- `spline(x, y)` returns a pp-form; `ppval`, `fnder` (Curve Fitting TB) — derivative of pp manually
  via `mkpp` if needed.
- Gridded 2D/3D: `griddedInterpolant`, `interp2`; scattered: `scatteredInterpolant`.
- High-degree polynomial interpolation on equispaced nodes → Runge phenomenon. Use Chebyshev
  nodes `x = cos((2*(1:n)-1)*pi/(2*n))` or piecewise methods.
- `polyfit(x, y, n)` is least squares; for degree > ~5 or large `x` use
  `[p, S, mu] = polyfit(x, y, n); yq = polyval(p, xq, [], mu);` (centering + scaling).
- Show the interpolation error on a fine grid, not only at the nodes.

### 5. Numerical integration

| Rule | Order (composite) | MATLAB |
|---|---|---|
| Trapezoid | h^2 | `trapz(x, y)`, `cumtrapz` (cumulative) |
| Simpson 1/3 | h^4 (n even) | write it: `h/3*(y(1) + 4*sum(y(2:2:end-1)) + 2*sum(y(3:2:end-2)) + y(end))` |
| Gauss–Legendre | 2n-1 exact | write nodes/weights (Golub–Welsch via `eig`) |
| Adaptive (Gauss–Kronrod) | — | `integral(f, a, b, 'RelTol',1e-10,'AbsTol',1e-12)` |

- `integral` needs a vectorized integrand (use `.*`, `./`, `.^`) or `'ArrayValued',true`.
- Infinite limits are allowed (`integral(f, 0, Inf)`); singular endpoints work if integrable but
  add `'Waypoints'` for interior kinks/singularities.
- Multi-dimensional: `integral2`, `integral3`; tabulated data: `trapz` along each dimension.
- Periodic smooth integrands: trapezoid converges spectrally — a nice observation for reports.

### 6. Numerical differentiation

- Forward difference `(f(x+h)-f(x))/h`: error ≈ `h/2 |f''| + 2 eps |f|/h` → optimal `h ≈ sqrt(eps)` ≈ 1e-8.
- Central difference `(f(x+h)-f(x-h))/(2h)`: O(h^2), optimal `h ≈ eps^(1/3)` ≈ 6e-6.
- Second derivative `(f(x+h) - 2f(x) + f(x-h))/h^2`: O(h^2), optimal `h ≈ eps^(1/4)` ≈ 1e-4.
- Demonstrate with a log-log plot of error vs `h` (V shape: truncation slope, then round-off).
- Tabulated data: `gradient(y, x)` (central inside, one-sided at ends). Noisy data: smooth or fit
  first (`smoothdata`, `sgolayfilt` from Signal TB), differentiating amplifies noise.
- Complex-step derivative `imag(f(x + 1i*h))/h` with `h = 1e-20` gives machine-precision first
  derivatives for real-analytic `f` (great trick for Jacobians).

## Appendix C: PDEs in MATLAB

### Contents
1. Choosing an approach
2. Grids, boundary conditions, sparse operators
3. Heat / diffusion equation (FTCS, BTCS, Crank–Nicolson)
4. Wave equation
5. Advection (upwind, Lax–Wendroff)
6. Laplace / Poisson (elliptic)
7. Method of lines with ode15s
8. pdepe
9. Verification and plots

### 1. Choosing an approach

| Situation | Approach |
|---|---|
| Course assignment on finite differences | write the scheme explicitly (sections 3–6) |
| 1D parabolic/elliptic system, quick and accurate | `pdepe` (section 8) |
| 1D/2D time-dependent, want adaptive time stepping | method of lines + `ode15s` with `JPattern` (section 7) |
| Complex 2D/3D geometry | PDE Toolbox (`createpde`, FEM) if available; otherwise say FD on rectangles only |

### 2. Grids, BCs, sparse operators

Uniform grid with `N` interior points: `x = linspace(a, b, N+2)`, `dx = (b-a)/(N+1)`, unknowns
`u(2:end-1)`. `fd_laplacian.m` (Appendix E) builds the sparse second-difference matrix for interior
points with Dirichlet boundaries in 1D or 2D (`kron` construction) and returns the boundary
contribution handled separately.

```matlab
e = ones(N,1);
D2 = spdiags([e -2*e e], -1:1, N, N) / dx^2;          % 1D, Dirichlet, interior points
L  = kron(speye(Ny), D2x) + kron(D2y, speye(Nx));     % 2D, unknowns ordered x-fastest
```
Dirichlet values enter the right-hand side: `b(1) += uL/dx^2`, `b(end) += uR/dx^2`.
Neumann `u_x = g` at the left: the boundary node becomes an unknown; ghost point `u_0 = u_2 - 2 dx g` → first row becomes
`[-2 2 0 …]/dx^2` and `b(1) -= 2g/dx`, keeping second order.

### 3. Heat equation `u_t = α u_xx`

`r = α dt / dx^2`.

| Scheme | Update | Accuracy | Stability |
|---|---|---|---|
| FTCS (explicit) | `u = u + r*(u(i+1) - 2u(i) + u(i-1))` | O(dt, dx²) | `r ≤ 1/2` |
| BTCS (implicit) | `(I - αdt D2) u^{n+1} = u^n` | O(dt, dx²) | unconditional |
| Crank–Nicolson | `(I - αdt/2 D2) u^{n+1} = (I + αdt/2 D2) u^n` | O(dt², dx²) | unconditional, can oscillate for large r with sharp ICs |

```matlab
A = speye(N) - 0.5*alpha*dt*D2;  B = speye(N) + 0.5*alpha*dt*D2;
dA = decomposition(A);            % factor once, reuse every step
for n = 1:nt
    u = dA \ (B*u + bc_terms);
end
```
For CN with discontinuous initial data, start with a few BTCS steps (Rannacher smoothing) if
oscillations appear. Exact solution for checks: `u = exp(-alpha*pi^2*t) .* sin(pi*x)` on [0,1].

### 4. Wave equation `u_tt = c² u_xx`

Leapfrog: `u^{n+1} = 2u^n - u^{n-1} + C²(u^n_{i+1} - 2u^n_i + u^n_{i-1})`, Courant number
`C = c dt / dx ≤ 1` (C = 1 is exact in 1D). First step from `u_t(x,0) = g`:
`u^1 = u^0 + dt g + (C²/2) δ²u^0`. Check energy conservation and d'Alembert's solution.

### 5. Advection `u_t + a u_x = 0`

Upwind (first order, diffusive), stable for `|a| dt/dx ≤ 1`, use the upwind side according to
`sign(a)`. Lax–Wendroff (second order, dispersive wiggles near jumps). FTCS for advection is
**unconditionally unstable** — a frequent student error. Compare with the exact shifted profile.

### 6. Laplace / Poisson `-∇²u = f`

Assemble `L` with `fd_laplacian`, move boundary values to the RHS, solve `u = -L\(f + bc)` (direct
sparse solve is fine up to ~10⁶ unknowns in 2D). Iterative alternatives for courses: Jacobi,
Gauss–Seidel, SOR with optimal ω; show iteration counts vs grid size. Plot with `surf` /
`contourf` after `reshape(u, Nx, Ny)'` (match the ordering used in `kron`).

### 7. Method of lines

Discretize space, integrate time with an ODE solver:
```matlab
rhs  = @(t,u) alpha*(D2*u + bc(t));
opts = odeset('JPattern', spones(D2), 'RelTol',1e-6, 'AbsTol',1e-8);  % or 'Jacobian', alpha*D2
[t, U] = ode15s(rhs, tvec, u0, opts);
```
Diffusion semi-discretizations are stiff (eigenvalues ~ -4α/dx²) → `ode15s`, never `ode45` on
fine grids. For nonlinear reaction–diffusion, pass the sparsity pattern of the full Jacobian.

### 8. pdepe

Solves 1D systems of the form `c(x,t,u,u_x) u_t = x^{-m} (x^m f)_x + s`, m = 0 slab, 1 cylinder,
2 sphere.
```matlab
m = 0; x = linspace(0,1,51); t = linspace(0,0.5,26);
sol = pdepe(m, @pdefun, @icfun, @bcfun, x, t);
u = sol(:,:,1);                               % rows = times, cols = x

function [c,f,s] = pdefun(x,t,u,dudx), c = 1; f = 0.1*dudx; s = 0; end
function u0 = icfun(x), u0 = sin(pi*x); end
function [pl,ql,pr,qr] = bcfun(xl,ul,xr,ur,t)  % p + q*f = 0 at each end
    pl = ul; ql = 0; pr = ur; qr = 0;          % Dirichlet u = 0 both ends
end
```
Neumann/flux conditions use `q` (with `f` the flux): e.g. insulated end `p = 0, q = 1`.
Use `pdeval` to evaluate at intermediate x. Needs at least ~3 time points; it chooses its own
internal steps. Not for hyperbolic problems.

### 9. Verification and plots

- Grid refinement: halve dx (and dt with the scheme's scaling, e.g. dt ∝ dx² for FTCS or dt ∝ dx
  for CN when checking second order) and compute errors in max norm / discrete L2 norm
  (`sqrt(dx*sum(e.^2))`); report observed orders with `conv_order.m`.
- Manufactured solutions: pick `u_exact`, compute the forcing `f` analytically, check the code
  reproduces `u_exact` at the expected order.
- Conservation (mass under Neumann BCs, energy for waves), maximum principle for heat.
- Plots: `surf(x, t, U)` with `shading interp` and labeled axes; snapshots at a few times on one
  axis; `imagesc` space–time diagrams for waves/advection; animations with `drawnow` loops or
  `VideoWriter` if the user wants a video.

## Appendix D: Modeling, fitting and parameter estimation

### Contents
1. Choosing a fitting tool (and toolbox fallbacks)
2. Linear least squares
3. Nonlinear curve fitting
4. Fitting ODE model parameters to data
5. Uncertainty: confidence intervals, residual analysis
6. Optimization with constraints
7. Model comparison and reporting

### 1. Choosing a tool

| Task | With toolbox | Base MATLAB fallback |
|---|---|---|
| Polynomial / linear-in-parameters | `fitlm` (Statistics) | `A\y`, `polyfit` |
| Nonlinear curve fit | `lsqcurvefit`, `lsqnonlin` (Optimization); `fitnlm` (Statistics) | `fminsearch` on sum of squares |
| Bounded/constrained | `lsqcurvefit` bounds, `fmincon` | parameter transforms + `fminsearch` |
| Global / many local minima | `MultiStart`, `ga` (Global Optimization) | loop over random starts with `rng(0)` |
| Confidence intervals | `nlparci`, `fitnlm` | Jacobian-based formula (section 5) |

Check availability: `license('test','Optimization_Toolbox')`, `license('test','Statistics_Toolbox')`,
or `exist('lsqcurvefit','file')`. Mention the fallback in the answer when unsure.

### 2. Linear least squares

Model linear in parameters, `y ≈ X β` (e.g. `y = a + b t + c e^{-t}`):
```matlab
X = [ones(size(t)) t exp(-t)];
beta = X \ y;                                   % QR-based least squares
r = y - X*beta;  dof = numel(y) - numel(beta);
s2 = (r'*r)/dof;  covb = s2 * inv(X'*X);        % here inv is acceptable: small matrix, covariance
se = sqrt(diag(covb));  R2 = 1 - sum(r.^2)/sum((y-mean(y)).^2);
```
Linearizing transforms (log of exponential models) change the error model; use them for initial
guesses, then refit the nonlinear model on the original data.

### 3. Nonlinear curve fitting

```matlab
model = @(p, t) p(1)*exp(-p(2)*t) + p(3);
p0 = [max(y)-min(y), 1/mean(t), min(y)];        % data-driven initial guess
lb = [0 0 -Inf]; ub = [Inf Inf Inf];
opts = optimoptions('lsqcurvefit','Display','off','FunctionTolerance',1e-12,'StepTolerance',1e-12);
[p, resnorm, res, exitflag, ~, ~, J] = lsqcurvefit(model, p0, t, y, lb, ub, opts);
```
Base-MATLAB fallback:
```matlab
sse = @(p) sum((y - model(p, t)).^2);
p = fminsearch(sse, p0, optimset('TolX',1e-10,'TolFun',1e-12,'MaxFunEvals',1e5,'MaxIter',1e5));
```
- Initial guesses decide success; derive them from the data (asymptotes, half-life, peak).
- Positive parameters spanning decades: fit `q = log(p)` and use `p = exp(q)`.
- Always check `exitflag` and plot data + fit + residuals.

### 4. Fitting ODE model parameters

```matlab
function r = residuals(q, tdata, ydata, y0)
    p = exp(q);                                          % positivity via log-parameters
    opts = odeset('RelTol',1e-8,'AbsTol',1e-10);         % solver error << data noise
    [~, Y] = ode45(@(t,y) rhs(t,y,p), tdata, y0, opts);  % tdata as tspan: outputs at data times
    r = Y(:,1) - ydata(:);   % tdata(1) must be the time of y0 (prepend t0 and drop that row if not)
end
q = lsqnonlin(@(q) residuals(q, tdata, ydata, y0), log(p0));
```
- Solver tolerance must be much tighter than the optimizer tolerance, or the objective becomes
  noisy and the optimizer stalls.
- Unknown initial conditions can be fitted as extra parameters.
- Weight states with different units/noise levels (divide residuals by their standard deviation).
- Identifiability: if parameters are strongly correlated (correlation matrix entries near ±1),
  say so; the data cannot determine them separately.
- Stiff models → `ode15s` inside the residual.

### 5. Uncertainty and residuals

From the Jacobian `J` at the optimum (returned by `lsqcurvefit`/`lsqnonlin`):
```matlab
n = numel(res); k = numel(p); dof = n - k;
s2 = sum(res.^2)/dof;
covp = s2 * inv(full(J'*J));
se = sqrt(diag(covp));
tcrit = tinv(0.975, dof);          % Statistics TB; fallback: 1.96 for large dof
ci = [p(:) - tcrit*se, p(:) + tcrit*se];
corrp = covp ./ (se*se');
```
(With log-parameters, transform the interval endpoints back with `exp`.) `nlparci(p,res,'jacobian',J)`
gives the same with the Statistics Toolbox. Residual checks: plot residuals vs. time/prediction
(no structure expected), histogram/QQ for normality, report RMSE and R².

### 6. Constrained optimization

`fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon, options)`; supply gradients when possible
(`'SpecifyObjectiveGradient',true`). Without the toolbox: bounds via transforms
(`x = lb + (ub-lb)./(1+exp(-z))`), penalties for simple constraints, then `fminsearch`.
Report the active constraints at the solution.

### 7. Model comparison and reporting

- Compare models with different numbers of parameters using AIC
  `n*log(SSE/n) + 2k` (lower is better) or held-out data, not R² alone.
- Report: model equation, parameter estimates ± standard error (or 95% CI) with units, RMSE, a
  figure with data, fit and residuals, and assumptions (independent errors, constant variance).
- Sensitivity: perturb each parameter ±10% and plot the model response, or compute normalized
  sensitivities `(p/y) ∂y/∂p` by finite differences.

## Appendix E: Helper files

### rk4.m

```matlab
function [t, Y] = rk4(f, tspan, y0, h)
%RK4 Classical fixed-step 4th-order Runge-Kutta for y' = f(t, y).
%   [t, Y] = rk4(f, [t0 tf], y0, h) integrates from t0 to tf with step h.
%   f must return a column vector. Output follows the ode45 convention:
%   t is a column vector, Y(k,:) is the solution at t(k).
%   If (tf - t0)/h is not an integer, the last step is shortened to hit tf.
%
%   Example:
%     [t, Y] = rk4(@(t,y) [y(2); -y(1)], [0 2*pi], [1; 0], 0.01);
%     max(abs(Y(:,1) - cos(t)))   % global error, O(h^4)

    t0 = tspan(1); tf = tspan(end);
    N  = ceil((tf - t0)/h - 1e-12);
    t  = t0 + (0:N)' * h;
    t(end) = tf;
    y  = y0(:);
    Y  = zeros(N+1, numel(y));
    Y(1,:) = y.';
    for n = 1:N
        hn = t(n+1) - t(n);
        k1 = f(t(n),        y);
        k2 = f(t(n) + hn/2, y + hn/2*k1);
        k3 = f(t(n) + hn/2, y + hn/2*k2);
        k4 = f(t(n) + hn,   y + hn*k3);
        y  = y + hn/6*(k1 + 2*k2 + 2*k3 + k4);
        Y(n+1,:) = y.';
    end
end
```

### conv_order.m

```matlab
function p = conv_order(h, e, varargin)
%CONV_ORDER Observed order of convergence.
%
%   p = conv_order(h, e)
%       h: step sizes (any order), e: errors against an exact/reference
%       solution. Returns the pairwise orders log(e_i/e_{i+1})/log(h_i/h_{i+1})
%       and, as the last element, the least-squares slope of log(e) vs log(h).
%
%   p = conv_order(h, u, 'self')
%       No exact solution: u are scalar results (e.g. u(T) or an integral)
%       computed with step sizes h, h/2, h/4, ... (refinement ratio may be any
%       constant). Uses differences of successive results:
%       p = log(|u1-u2|/|u2-u3|)/log(ratio).
%
%   conv_order(...) with no output prints a table and makes a log-log plot.
%
%   Example:
%     h = 0.1./2.^(0:4);
%     e = arrayfun(@(hh) abs(trapz(0:hh:1, exp(0:hh:1)) - (exp(1)-1)), h);
%     conv_order(h, e)        % ~2 for the trapezoid rule

    h = h(:); e = e(:);
    [h, idx] = sort(h, 'descend'); e = e(idx);
    selfMode = ~isempty(varargin) && strcmpi(varargin{1}, 'self');

    if selfMode
        d = abs(diff(e));                 % |u_k - u_{k+1}| behaves like C h_k^p
        r = h(1:end-2) ./ h(2:end-1);
        p = log(d(1:end-1) ./ d(2:end)) ./ log(r);
        hp = h(1:end-1); ep = d;          % for plotting
    else
        p = log(e(1:end-1) ./ e(2:end)) ./ log(h(1:end-1) ./ h(2:end));
        c = polyfit(log(h), log(e), 1);
        p = [p; c(1)];
        hp = h; ep = e;
    end

    if nargout == 0
        fprintf('%12s %14s %10s\n', 'h', 'error', 'order');
        for k = 1:numel(hp)
            if k == 1
                fprintf('%12.4e %14.6e %10s\n', hp(k), ep(k), '-');
            else
                fprintf('%12.4e %14.6e %10.3f\n', hp(k), ep(k), p(k-1));
            end
        end
        if ~selfMode, fprintf('least-squares slope: %.3f\n', p(end)); end
        figure; loglog(hp, ep, 'o-', 'LineWidth', 1.5); hold on
        s = round(p(end));
        loglog(hp, ep(1)*(hp/hp(1)).^s, 'k--');
        grid on; xlabel('step size h'); ylabel('error');
        legend('observed', sprintf('slope %d reference', s), 'Location', 'best');
        title('Convergence study'); clear p
    end
end
```

### fd_laplacian.m

```matlab
function [L, applyBC] = fd_laplacian(N, h)
%FD_LAPLACIAN Sparse 2nd-order finite-difference Laplacian, Dirichlet BCs.
%
%   1D:  [L, applyBC] = fd_laplacian(N, h)
%        N interior points with spacing h on [a, b] (h = (b-a)/(N+1)).
%        L is N-by-N, L*u approximates u'' at the interior points when the
%        boundary values are zero. applyBC(uL, uR) returns the N-by-1 vector
%        that must be ADDED to L*u for nonzero boundary values:
%            u'' ~ L*u + applyBC(uL, uR)
%
%   2D:  [L, applyBC] = fd_laplacian([Nx Ny], [hx hy])
%        Unknowns u(i,j), i = 1..Nx (x), j = 1..Ny (y), stored as u(:) with
%        x varying fastest (U = reshape(u, Nx, Ny)). L is (Nx*Ny)-square.
%        applyBC(gW, gE, gS, gN) takes boundary values on the West (x = a,
%        Ny-by-1), East (x = b, Ny-by-1), South (y = c, Nx-by-1) and North
%        (y = d, Nx-by-1) sides and returns the vector to add to L*u.
%
%   Example (Poisson -u'' = f on (0,1), u(0) = 0, u(1) = 1):
%     N = 99; h = 1/(N+1); x = (1:N)'*h;
%     [L, bc] = fd_laplacian(N, h);
%     u = -L \ (f(x) + bc(0, 1));       % from -(L*u + bc) = f

    if isscalar(N)
        e  = ones(N, 1);
        L  = spdiags([e -2*e e], -1:1, N, N) / h^2;
        applyBC = @(uL, uR) [uL; zeros(N-2, 1); uR] / h^2;
        if N == 1, applyBC = @(uL, uR) (uL + uR) / h^2; end
        return
    end

    Nx = N(1); Ny = N(2);
    if isscalar(h), h = [h h]; end
    hx = h(1); hy = h(2);
    ex = ones(Nx, 1); ey = ones(Ny, 1);
    Dx = spdiags([ex -2*ex ex], -1:1, Nx, Nx) / hx^2;
    Dy = spdiags([ey -2*ey ey], -1:1, Ny, Ny) / hy^2;
    L  = kron(speye(Ny), Dx) + kron(Dy, speye(Nx));

    applyBC = @(gW, gE, gS, gN) bc2d(gW, gE, gS, gN, Nx, Ny, hx, hy);
end

function b = bc2d(gW, gE, gS, gN, Nx, Ny, hx, hy)
    B = zeros(Nx, Ny);
    B(1, :)   = B(1, :)   + gW(:).' / hx^2;
    B(end, :) = B(end, :) + gE(:).' / hx^2;
    B(:, 1)   = B(:, 1)   + gS(:)   / hy^2;
    B(:, end) = B(:, end) + gN(:)   / hy^2;
    b = B(:);
end
```

### study_template.m

```matlab
%% <Title of the study>
% Problem: <one-paragraph statement: equations, domain, initial/boundary
%          conditions, what quantity we want>
% Method : <solver/scheme and why (stiff? order? stability?)>
% Author : <name>        Date: <date>        MATLAB <version>
clear; close all; clc

%% 1. Parameters (with units)
p.k  = 4.0;      % stiffness [N/m]
p.c  = 0.2;      % damping   [N s/m]
p.m  = 1.0;      % mass      [kg]
y0   = [1; 0];   % [position (m); velocity (m/s)]
tf   = 20;       % final time [s]

%% 2. Solve
opts  = odeset('RelTol', 1e-8, 'AbsTol', 1e-10);
tspan = linspace(0, tf, 1001);
[t, Y] = ode45(@(t, y) rhs(t, y, p), tspan, y0, opts);

%% 3. Verify
% (a) tolerance check: results must not change at the reported digits
optsTight = odeset('RelTol', 1e-11, 'AbsTol', 1e-13);
[~, Yt] = ode45(@(t, y) rhs(t, y, p), tspan, y0, optsTight);
fprintf('max change with 1000x tighter tolerances: %.2e\n', max(abs(Y(:) - Yt(:))));
% (b) exact / reference solution, invariant, or convergence study here
%     e.g. energy E = 0.5*m*v.^2 + 0.5*k*x.^2 should decay monotonically (c > 0)
E = 0.5*p.m*Y(:,2).^2 + 0.5*p.k*Y(:,1).^2;
fprintf('energy monotonically non-increasing: %d\n', all(diff(E) <= 1e-8*max(E)));

%% 4. Results
fprintf('x(tf) = %.6f m\n', Y(end, 1));

figure('Color', 'w');
tiledlayout(2, 1);
nexttile; plot(t, Y(:,1), 'LineWidth', 1.5); grid on
xlabel('t [s]'); ylabel('x [m]'); title('Displacement');
nexttile; plot(t, E, 'LineWidth', 1.5); grid on
xlabel('t [s]'); ylabel('E [J]'); title('Mechanical energy');
% exportgraphics(gcf, 'results.png', 'Resolution', 200);   % R2020a+

%% Local functions
function dydt = rhs(~, y, p)
    % y(1) = position, y(2) = velocity
    dydt = [y(2);
            (-p.c*y(2) - p.k*y(1)) / p.m];
end
```
