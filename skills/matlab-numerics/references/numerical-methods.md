# Core numerical methods in MATLAB

## Contents
1. Error, floating point, convergence order
2. Root finding (scalar) and nonlinear systems
3. Linear systems
4. Interpolation and approximation
5. Numerical integration
6. Numerical differentiation

## 1. Error, floating point, convergence

- `eps` ≈ 2.2e-16 (relative spacing at 1). Report relative error `abs(x - xref)/abs(xref)` when
  magnitudes vary.
- Order of convergence: if `e(h) ≈ C h^p`, then `p ≈ log(e1/e2)/log(h1/h2)`. Plot `loglog(h, e)`
  with a reference slope line. Without an exact solution use three refinements:
  `p ≈ log2(|u_h - u_{h/2}| / |u_{h/2} - u_{h/4}|)`. Both are in `scripts/conv_order.m`.
- Iterative methods: linear convergence `e_{k+1} ≈ C e_k`; quadratic (Newton) `e_{k+1} ≈ C e_k^2`.
  Show a table of `k, x_k, |f(x_k)|, |x_k - x_{k-1}|`.
- Richardson extrapolation: `(2^p u_{h/2} - u_h)/(2^p - 1)` improves accuracy by one order.
- Total error = truncation + round-off; there is an optimal step for differences (section 6).

## 2. Root finding

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

## 3. Linear systems

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

## 4. Interpolation and approximation

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

## 5. Numerical integration

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

## 6. Numerical differentiation

- Forward difference `(f(x+h)-f(x))/h`: error ≈ `h/2 |f''| + 2 eps |f|/h` → optimal `h ≈ sqrt(eps)` ≈ 1e-8.
- Central difference `(f(x+h)-f(x-h))/(2h)`: O(h^2), optimal `h ≈ eps^(1/3)` ≈ 6e-6.
- Second derivative `(f(x+h) - 2f(x) + f(x-h))/h^2`: O(h^2), optimal `h ≈ eps^(1/4)` ≈ 1e-4.
- Demonstrate with a log-log plot of error vs `h` (V shape: truncation slope, then round-off).
- Tabulated data: `gradient(y, x)` (central inside, one-sided at ends). Noisy data: smooth or fit
  first (`smoothdata`, `sgolayfilt` from Signal TB), differentiating amplifies noise.
- Complex-step derivative `imag(f(x + 1i*h))/h` with `h = 1e-20` gives machine-precision first
  derivatives for real-analytic `f` (great trick for Jacobians).
