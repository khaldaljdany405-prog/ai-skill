# PDEs in MATLAB

## Contents
1. Choosing an approach
2. Grids, boundary conditions, sparse operators
3. Heat / diffusion equation (FTCS, BTCS, Crank–Nicolson)
4. Wave equation
5. Advection (upwind, Lax–Wendroff)
6. Laplace / Poisson (elliptic)
7. Method of lines with ode15s
8. pdepe
9. Verification and plots

## 1. Choosing an approach

| Situation | Approach |
|---|---|
| Course assignment on finite differences | write the scheme explicitly (sections 3–6) |
| 1D parabolic/elliptic system, quick and accurate | `pdepe` (section 8) |
| 1D/2D time-dependent, want adaptive time stepping | method of lines + `ode15s` with `JPattern` (section 7) |
| Complex 2D/3D geometry | PDE Toolbox (`createpde`, FEM) if available; otherwise say FD on rectangles only |

## 2. Grids, BCs, sparse operators

Uniform grid with `N` interior points: `x = linspace(a, b, N+2)`, `dx = (b-a)/(N+1)`, unknowns
`u(2:end-1)`. `scripts/fd_laplacian.m` builds the sparse second-difference matrix for interior
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

## 3. Heat equation `u_t = α u_xx`

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

## 4. Wave equation `u_tt = c² u_xx`

Leapfrog: `u^{n+1} = 2u^n - u^{n-1} + C²(u^n_{i+1} - 2u^n_i + u^n_{i-1})`, Courant number
`C = c dt / dx ≤ 1` (C = 1 is exact in 1D). First step from `u_t(x,0) = g`:
`u^1 = u^0 + dt g + (C²/2) δ²u^0`. Check energy conservation and d'Alembert's solution.

## 5. Advection `u_t + a u_x = 0`

Upwind (first order, diffusive), stable for `|a| dt/dx ≤ 1`, use the upwind side according to
`sign(a)`. Lax–Wendroff (second order, dispersive wiggles near jumps). FTCS for advection is
**unconditionally unstable** — a frequent student error. Compare with the exact shifted profile.

## 6. Laplace / Poisson `-∇²u = f`

Assemble `L` with `fd_laplacian`, move boundary values to the RHS, solve `u = -L\(f + bc)` (direct
sparse solve is fine up to ~10⁶ unknowns in 2D). Iterative alternatives for courses: Jacobi,
Gauss–Seidel, SOR with optimal ω; show iteration counts vs grid size. Plot with `surf` /
`contourf` after `reshape(u, Nx, Ny)'` (match the ordering used in `kron`).

## 7. Method of lines

Discretize space, integrate time with an ODE solver:
```matlab
rhs  = @(t,u) alpha*(D2*u + bc(t));
opts = odeset('JPattern', spones(D2), 'RelTol',1e-6, 'AbsTol',1e-8);  % or 'Jacobian', alpha*D2
[t, U] = ode15s(rhs, tvec, u0, opts);
```
Diffusion semi-discretizations are stiff (eigenvalues ~ -4α/dx²) → `ode15s`, never `ode45` on
fine grids. For nonlinear reaction–diffusion, pass the sparsity pattern of the full Jacobian.

## 8. pdepe

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

## 9. Verification and plots

- Grid refinement: halve dx (and dt with the scheme's scaling, e.g. dt ∝ dx² for FTCS or dt ∝ dx
  for CN when checking second order) and compute errors in max norm / discrete L2 norm
  (`sqrt(dx*sum(e.^2))`); report observed orders with `conv_order.m`.
- Manufactured solutions: pick `u_exact`, compute the forcing `f` analytically, check the code
  reproduces `u_exact` at the expected order.
- Conservation (mass under Neumann BCs, energy for waves), maximum principle for heat.
- Plots: `surf(x, t, U)` with `shading interp` and labeled axes; snapshots at a few times on one
  axis; `imagesc` space–time diagrams for waves/advection; animations with `drawnow` loops or
  `VideoWriter` if the user wants a video.
