# Modeling, fitting and parameter estimation

## Contents
1. Choosing a fitting tool (and toolbox fallbacks)
2. Linear least squares
3. Nonlinear curve fitting
4. Fitting ODE model parameters to data
5. Uncertainty: confidence intervals, residual analysis
6. Optimization with constraints
7. Model comparison and reporting

## 1. Choosing a tool

| Task | With toolbox | Base MATLAB fallback |
|---|---|---|
| Polynomial / linear-in-parameters | `fitlm` (Statistics) | `A\y`, `polyfit` |
| Nonlinear curve fit | `lsqcurvefit`, `lsqnonlin` (Optimization); `fitnlm` (Statistics) | `fminsearch` on sum of squares |
| Bounded/constrained | `lsqcurvefit` bounds, `fmincon` | parameter transforms + `fminsearch` |
| Global / many local minima | `MultiStart`, `ga` (Global Optimization) | loop over random starts with `rng(0)` |
| Confidence intervals | `nlparci`, `fitnlm` | Jacobian-based formula (section 5) |

Check availability: `license('test','Optimization_Toolbox')`, `license('test','Statistics_Toolbox')`,
or `exist('lsqcurvefit','file')`. Mention the fallback in the answer when unsure.

## 2. Linear least squares

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

## 3. Nonlinear curve fitting

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

## 4. Fitting ODE model parameters

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

## 5. Uncertainty and residuals

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

## 6. Constrained optimization

`fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon, options)`; supply gradients when possible
(`'SpecifyObjectiveGradient',true`). Without the toolbox: bounds via transforms
(`x = lb + (ub-lb)./(1+exp(-z))`), penalties for simple constraints, then `fminsearch`.
Report the active constraints at the solution.

## 7. Model comparison and reporting

- Compare models with different numbers of parameters using AIC
  `n*log(SSE/n) + 2k` (lower is better) or held-out data, not R² alone.
- Report: model equation, parameter estimates ± standard error (or 95% CI) with units, RMSE, a
  figure with data, fit and residuals, and assumptions (independent errors, constant variance).
- Sensitivity: perturb each parameter ±10% and plot the model response, or compute normalized
  sensitivities `(p/y) ∂y/∂p` by finite differences.
