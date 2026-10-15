function [X0, ZLc, Iall] = mtsf_seed(prob, reg)
%MTSF_SEED  Analytic seed (paper Sec. III/IV): synthesise port currents for each 'match' state
%   with eq.(8), convert to complex loads with eq.(5), keep the imaginary part (eq.9 seed).
%   Several states -> imaginary parts averaged.  Mask states are seeded with zeros.
if nargin<2, reg = 1e-6; end
iL = prob.iL; iE = prob.iE; N = numel(iL);
Xs = []; ZLc = []; Iall = [];
for s = 1:numel(prob.states)
    st = prob.states(s);
    if isfield(st,'type') && strcmp(st.type,'mask'), continue; end
    if st.sgn > 0                                      % directly fed: Edes produced by all M ports
        I = mtsf_synth_currents(prob.F, st.Edes, prob.w, reg);
        IE = st.IE; scale = IE(1)/I(iE(1));            % match the actual feed current
        I = I*scale; IL = I(iL);
    else                                               % reflective: F_L I_L = E_s|open - Edes, eq.(16)
        Ed = st.Edes; 
        if any(st.E0), sc = (Ed'*([prob.w;prob.w].*st.E0))/(Ed'*([prob.w;prob.w].*Ed)); else, sc = 1; end
        IL = mtsf_synth_currents(prob.F(:,iL), st.E0 - sc*Ed, prob.w, reg);
        % The incident amplitude fixes |v_oc| but not the current level that best suits a passive
        % lossless surface: pick the complex scale 1/t that makes eq.(5) as reactive as possible,
        % i.e. min_t || Re( t*(Vexc./IL) - (Z_LL IL)./IL ) ||^2  (2-unknown least squares).
        a = st.Vexc./IL; b = (prob.Z(iL,iL)*IL)./IL;
        tt = [real(a), -imag(a)] \ real(b); t = tt(1)+1j*tt(2);
        IL = IL/t; I = IL;
    end
    Zc = mtsf_loads_from_currents(prob.Z(iL,iL), IL, st.Vexc);
    ZLc = [ZLc, Zc]; Xs = [Xs, imag(Zc)]; Iall = [Iall, I];
end
if isempty(Xs), X0 = zeros(N,1); else, X0 = mean(Xs,2); end
end
