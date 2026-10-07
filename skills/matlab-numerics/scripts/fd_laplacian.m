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
