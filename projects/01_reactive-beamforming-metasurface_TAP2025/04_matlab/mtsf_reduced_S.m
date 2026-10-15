function [S, Zr] = mtsf_reduced_S(Z, iL, iE, X, Z0)
%MTSF_REDUCED_S  Scattering matrix seen at the K excitation ports, eqs.(12)-(14).
%   Zr = Z_EE - Z_EL (jX + Z_LL)^{-1} Z_LE ;   S = (Zr + Z0)^{-1} (Zr - Z0)
if nargin<5, Z0 = 50; end
A  = Z(iL,iL) + 1j*diag(X);
Zr = Z(iE,iE) - Z(iE,iL) * (A \ Z(iL,iE));
K  = numel(iE); Z0m = Z0*eye(K);
S  = (Zr + Z0m) \ (Zr - Z0m);
end
