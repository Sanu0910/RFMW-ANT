function [IL, A] = mtsf_currents_from_loads(Zll, X, Vexc)
%MTSF_CURRENTS_FROM_LOADS  Load currents for purely reactive loads, eq.(9):
%   I_L = (j X_L + Z_LL)^{-1} V_exc
A  = Zll + 1j*diag(X);
IL = A \ Vexc;
end
