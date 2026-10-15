function [X, info] = mtsf_optimize(prob, X0, lb, ub, maxit)
%MTSF_OPTIMIZE  Bounded minimisation of mtsf_cost over the reactances (paper Sec. IV, fmincon).
%   MATLAB : fmincon (sqp) with the analytic gradient.
%   Octave / no toolbox : projected L-BFGS with Armijo backtracking (same analytic gradient).
%   lb/ub bound X to the range your load technology can realise (e.g. +-150 ohm for
%   meandered open stubs inside a lambda/5 cell, varactor C-range for a reconfigurable surface).
if nargin<5, maxit = 300; end
X0 = min(max(X0(:),lb(:)),ub(:));
f  = @(x) mtsf_cost(x, prob);
if exist('fmincon','file') == 2
    opt = optimoptions('fmincon','Algorithm','sqp','SpecifyObjectiveGradient',true, ...
          'MaxIterations',maxit,'MaxFunctionEvaluations',20*maxit,'Display','iter', ...
          'OptimalityTolerance',1e-8,'StepTolerance',1e-10);
    [X,fval,flag] = fmincon(f, X0, [],[],[],[], lb(:), ub(:), [], opt);
    info = struct('J',fval,'flag',flag,'solver','fmincon');
else                                   % Octave / no Optimization Toolbox
    [X, fval, it] = plbfgs(f, X0, lb(:), ub(:), maxit);
    info = struct('J',fval,'flag',0,'iter',it,'solver','projected L-BFGS');
end
end
function g = grad_only(x, prob)
[~, g] = mtsf_cost(x, prob);
end
function [x, J, it] = plbfgs(f, x, lb, ub, maxit)
m = 20; Sm = []; Ym = []; [J,g] = f(x);
for it = 1:maxit
    q = g; a = zeros(size(Sm,2),1);                     % two-loop recursion
    for i = size(Sm,2):-1:1, rho = 1/(Ym(:,i)'*Sm(:,i)); a(i) = rho*Sm(:,i)'*q; q = q - a(i)*Ym(:,i); end
    if isempty(Sm), q = q*(1/max(norm(g),1e-12))*10; else, q = q*(Sm(:,end)'*Ym(:,end))/(Ym(:,end)'*Ym(:,end)); end
    for i = 1:size(Sm,2), rho = 1/(Ym(:,i)'*Sm(:,i)); b = rho*Ym(:,i)'*q; q = q + Sm(:,i)*(a(i)-b); end
    dvec = -q; if g'*dvec >= 0, dvec = -g; Sm = []; Ym = []; end
    t = 1;
    while true
        xn = min(max(x + t*dvec, lb), ub); [Jn,gn] = f(xn);
        if Jn <= J + 1e-4*g'*(xn-x) || t < 1e-10, break; end
        t = t/2;
    end
    s_ = xn - x; y_ = gn - g;
    if s_'*y_ > 1e-12, Sm = [Sm s_]; Ym = [Ym y_]; if size(Sm,2) > m, Sm(:,1) = []; Ym(:,1) = []; end; end
    conv = abs(J-Jn) < 1e-10*max(1,abs(J)) || norm(s_) < 1e-9;
    x = xn; J = Jn; g = gn;
    if conv, break; end
end
end
