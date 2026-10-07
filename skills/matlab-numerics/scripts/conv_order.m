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
