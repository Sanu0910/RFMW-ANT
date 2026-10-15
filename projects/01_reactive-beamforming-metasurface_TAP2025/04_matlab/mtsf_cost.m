function [J, grad, out] = mtsf_cost(X, prob)
%MTSF_COST  Optimisation cost of eq.(11) with analytic gradient w.r.t. the load reactances X.
%
%   g = alpha * sum_states J_pattern  +  beta * sum_i |S_ii|  +  gamma * sum_{i<j} |S_ij|
%
%   Pattern term (per excitation state s):
%     'match' : J = 1 - |<Edes,E>|^2 / (<Edes,Edes><E,E>)   (normalised |Edes-Etot|^2 with the
%               optimal free complex scale - the paper's raw |Edes-Etot|^2 depends on the absolute
%               field level, which is set by the source/plane-wave amplitude, not by the loads)
%     'mask'  : flat-top / sidelobe mask (Design II): variance of |E|^2 in the main region +
%               penalty on |E|^2 above SLL in the sidelobe region, both relative to the main mean.
%   Field per state:  E = E0 + sgn * F_L * I_L,   I_L = (jX + Z_LL)^{-1} V_exc   (eqs.9,10,15)
%     directly fed  : V_exc = -Z_LE*I_E,  E0 = F_E*I_E,          sgn = +1   (eq.10)
%     reflective    : V_exc = v_oc,       E0 = E_s|open,         sgn = -1   (eq.15)
%   S-terms use the reduced matrix of eqs.(13)-(14) (directly fed only).
%
%   prob fields: Z, iL, iE, F (2Na x M), w (Na x 1), Z0, alpha, beta, gamma, states(:)
%   states(s): Vexc, E0, sgn, type ('match'|'mask'), Edes | main, side, sll_dB, wside
X  = X(:);
iL = prob.iL; N = numel(iL);
A  = prob.Z(iL,iL) + 1j*diag(X);
[Lf,Uf,Pf] = lu(A);                                   % one factorisation per evaluation
solveA  = @(B) Uf\(Lf\(Pf*B));                         % A^{-1} B
solveAt = @(B) Pf.'*(Lf.'\(Uf.'\B));                   % A^{-T} B
FL = prob.F(:,iL); W = [prob.w; prob.w];
J = 0; grad = zeros(N,1); out.Jpat = zeros(numel(prob.states),1); out.E = cell(numel(prob.states),1);
for s = 1:numel(prob.states)
    st = prob.states(s);
    IL = solveA(st.Vexc);
    E  = st.E0 + st.sgn*(FL*IL);
    out.E{s} = E; out.IL{s} = IL;
    if ~isfield(st,'type') || isempty(st.type) || strcmp(st.type,'match')
        Ed = st.Edes;
        a = Ed'*(W.*E); e = real(Ed'*(W.*Ed)); p = real(E'*(W.*E));
        p = max(p, realmin); Js = 1 - abs(a)^2/(e*p);
        xa = solveAt( ((W.*Ed)'*FL).' ).';            % (Edes^H W F_L) A^{-1}
        xp = solveAt( ((W.*E )'*FL).' ).';            % (E^H W F_L) A^{-1}
        da = -1j*st.sgn*(xa.'.*IL);
        dp = 2*real(-1j*st.sgn*(xp.'.*IL));
        g  = -(2*real(conj(a)*da)*p - abs(a)^2*dp)/(e*p^2);
    else                                               % 'mask'
        Na = numel(prob.w);
        U  = abs(E(1:Na)).^2 + abs(E(Na+1:end)).^2;
        mn = st.main; sd = st.side; Nm = nnz(mn); Ns = max(nnz(sd),1);
        m  = sum(prob.w(mn).*U(mn))/sum(prob.w(mn));   % weighted mean in main region
        r  = U/m; t = 10^(st.sll_dB/10); h = max(0, r - t).*sd;
        wm = prob.w(mn)/sum(prob.w(mn)); ws = prob.w.*sd/sum(prob.w(sd));
        Js = sum(wm.*(r(mn)-1).^2) + st.wside*sum(ws.*h.^2);
        q = zeros(Na,1);                               % dJ/dU
        c1 = sum(wm.*(r(mn)-1).*r(mn));
        q(mn) = 2*wm.*(r(mn)-1)/m - 2*c1*wm/m;
        c2 = sum(ws.*h.*r);
        q(sd) = q(sd) + 2*st.wside*ws(sd).*h(sd)/m;
        q(mn) = q(mn) - 2*st.wside*c2*wm/m;
        q2 = [q; q];
        v  = solveAt( ((q2.*conj(E)).'*FL).' ).';
        g  = 2*real(-1j*st.sgn*(v.'.*IL));
    end
    J = J + prob.alpha*Js; grad = grad + prob.alpha*g; out.Jpat(s) = Js;
end
iE = prob.iE; K = numel(iE);
if K>0 && (prob.beta>0 || prob.gamma>0)
    ZLE = prob.Z(iL,iE); ZEL = prob.Z(iE,iL);
    B2 = solveA(ZLE);                                  % A^{-1} Z_LE   (N x K)
    B1 = solveAt(ZEL.').';                             % Z_EL A^{-1}   (K x N)
    Zr = prob.Z(iE,iE) - ZEL*B2;
    Z0m = prob.Z0*eye(K);
    S  = (Zr+Z0m)\(Zr-Z0m);
    C1 = (Zr+Z0m)\B1;  C2 = B2*(eye(K)-S);             % dS_n = j C1(:,n) C2(n,:)
    for i = 1:K
        dSii = 1j*C1(i,:).'.*C2(:,i);
        J = J + prob.beta*abs(S(i,i));
        grad = grad + prob.beta*real(conj(S(i,i))*dSii)/max(abs(S(i,i)),1e-12);
        for j = i+1:K
            dSij = 1j*C1(i,:).'.*C2(:,j);
            J = J + prob.gamma*abs(S(i,j));
            grad = grad + prob.gamma*real(conj(S(i,j))*dSij)/max(abs(S(i,j)),1e-12);
        end
    end
    out.S = S; out.Zr = Zr;
end
end
