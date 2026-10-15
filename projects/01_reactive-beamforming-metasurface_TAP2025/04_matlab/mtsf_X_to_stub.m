function [L_mm, info] = mtsf_X_to_stub(X, f, w_mm, h_mm, er)
%MTSF_X_TO_STUB  Open-circuited microstrip stub length giving input reactance X (Sec. VII).
%   Zin = -j Zc cot(beta l)  ->  beta l = atan2(1, -X/Zc),  0 < beta l < pi
%   Hammerstad eps_eff / Zc and open-end extension dl are included.  Treat as a FIRST GUESS:
%   meander bends, coupling to the slot and to neighbours shift X - extract Zin(L) in HFSS
%   (05_python_tools/build_dxf.py --table) for the final lengths, as the paper does.
if nargin<2, f = 10e9; end
if nargin<3, w_mm = 0.4; end
if nargin<4, h_mm = 0.203; end
if nargin<5, er = 3.55; end
u  = w_mm/h_mm;
ee = (er+1)/2 + (er-1)/2*(1+12/u)^-0.5;
if u <= 1, Zc = 60/sqrt(ee)*log(8/u+u/4);
else,      Zc = 120*pi/(sqrt(ee)*(u+1.393+0.667*log(u+1.444))); end
dl  = 0.412*h_mm*(ee+0.3)*(u+0.264)/((ee-0.258)*(u+0.8));
lamg = 299.792458/(f/1e9)/sqrt(ee);
bl   = atan2(1, -X/Zc);
L_mm = max(bl/(2*pi)*lamg - dl, 0.3);
info = struct('eps_eff',ee,'Zc',Zc,'lambda_g_mm',lamg,'dl_open_mm',dl);
end
