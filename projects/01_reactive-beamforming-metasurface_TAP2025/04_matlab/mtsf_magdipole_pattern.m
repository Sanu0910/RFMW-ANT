function [Eth,Eph] = mtsf_magdipole_pattern(ang)
%MTSF_MAGDIPOLE_PATTERN  Normalised y-directed magnetic-dipole element pattern, eq.(22):
%   E = -cos(phi) theta_hat + cos(theta) sin(phi) phi_hat
Eth = -cos(ang.phi);
Eph =  cos(ang.theta).*sin(ang.phi);
end
