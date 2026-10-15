function [C, V] = ns_varactor_cv(V, Vmax)
%NS_VARACTOR_CV  Hyperabrupt C(V) fitted to C(0)=1.7 pF, C(Vmax)=0.14 pF.  [ASSUMED model]
%   Replace by the MAVR-000120-14110P datasheet table / SPICE model before using a bias LUT.
if nargin<2, Vmax = 15; end
Cp = 0.05e-12; C0j = 1.7e-12; Cmin = 0.14e-12; Vbi = 0.8;
g = log((C0j-Cp)/(Cmin-Cp))/log(1+Vmax/Vbi);
C = Cp + (C0j-Cp)./(1+V/Vbi).^g;
end
