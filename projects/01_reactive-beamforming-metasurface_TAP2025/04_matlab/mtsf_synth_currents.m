function I = mtsf_synth_currents(F, Edes, w, reg)
%MTSF_SYNTH_CURRENTS  Port currents that best produce Edes, eqs.(6)-(8).
%   F    : 2Na x M stacked element patterns [Eth; Eph] (current basis, 1 A, others open)
%   Edes : 2Na x 1 desired field;  w : Na x 1 quadrature weights
%   reg  : Tikhonov factor (default 1e-6). The Gram matrix of eq.(8) is ill-conditioned for
%          sub-wavelength cells (evanescent spectrum is invisible in the far field), so a small
%          regularisation keeps the currents (and therefore the loads) bounded.
if nargin<4, reg = 1e-6; end
W  = [w; w];
G  = F' * (W .* F);                    % eq.(8) matrix:  <E_m, E_n>
b  = F' * (W .* Edes);                 % eq.(8) RHS:     <E_m, E_des>
M  = size(G,1);
I  = (G + reg*real(trace(G))/M*eye(M)) \ b;
end
