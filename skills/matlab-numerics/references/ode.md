# ODEs in MATLAB

## Contents
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

## 1. Reducing to a first-order system

`m x'' + c x' + k x = F(t)` → `y = [x; v]`, `y' = [v; (F(t) - c v - k x)/m]`.
For an n-th order equation, introduce y1 = x, y2 = x', …, yn = x^(n-1). State the meaning of each
component in a comment.

```matlab
p = struct('m',1,'c',0.2,'k',4,'F0',1,'w',1.5);
rhs = @(t,y) [y(2); (p.F0*cos(p.w*t) - p.c*y(2) - p.k*y(1))/p.m];
```

## 2. Choosing a solver

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

## 3. Standard solve pattern

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

## 4. Stiffness

Signs: `ode45` takes a huge number of tiny steps although the solution is smooth; Jacobian
eigenvalues with very different magnitudes (`max|Re λ| / min|Re λ|` large) and negative real
parts; chemical kinetics, circuits, fast-slow systems, semi-discretized diffusion PDEs.

Do: switch to `ode15s` (or `ode23s`/`ode23tb`), supply the Jacobian (`'Jacobian',@J`) or at least
its sparsity pattern (`'JPattern',S`) for large systems — this is the biggest speedup for method
of lines. Show `Stats` of both solvers to demonstrate the difference.

Classic demo: Van der Pol with `mu = 1000`, Robertson chemical kinetics.

## 5. Events

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

## 6. Mass matrices and DAEs

`M(t,y) y' = f(t,y)` with singular `M` = semi-explicit DAE (index 1).
```matlab
opts = odeset('Mass', M, 'MassSingular','yes', 'RelTol',1e-6);
[t, Y] = ode15s(f, tspan, y0consistent, opts);
```
Initial conditions must be consistent with the algebraic equations (`decic` helps for `ode15i`).
Higher-index DAEs need index reduction first.

## 7. Boundary value problems

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

## 8. Delay equations

```matlab
lags = 1;                                   % y'(t) = -y(t-1)
ddefun = @(t,y,Z) -Z(:,1);                  % Z(:,j) = y(t - lags(j))
sol = dde23(ddefun, lags, @(t) 1, [0 10]);  % history function for t <= 0
```

## 9. Hand-written methods (when the assignment asks)

Use `scripts/rk4.m` for fixed-step RK4 on systems. Explicit Euler in a few lines:
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

## 10. Phase portraits and stability

- Equilibria: solve `f(y) = 0` (`fzero` in 1D, `fsolve` or Newton in nD).
- Jacobian at equilibria (analytic or finite differences) → `eig(J)`: all `Re < 0` stable node/
  focus, mixed signs saddle, purely imaginary → center for the linearization (inconclusive).
- Direction field: `quiver` on a `meshgrid` of normalized `f`; overlay trajectories from several
  initial conditions; mark equilibria.

## 11. Parameter sweeps

Loop over parameter values with preallocated outputs; extract a scalar quantity per run (peak,
period, final value) and plot it against the parameter (bifurcation-style diagram). For many
runs use `parfor` only if the Parallel Toolbox is available.
