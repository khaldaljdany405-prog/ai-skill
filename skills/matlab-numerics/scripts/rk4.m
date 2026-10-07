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
