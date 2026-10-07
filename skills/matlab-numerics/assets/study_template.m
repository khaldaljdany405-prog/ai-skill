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
