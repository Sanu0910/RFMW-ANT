function [ph, dphi] = ns_phases_1d(theta_null_deg, f, mid)
%NS_PHASES_1D  Phase-shifter settings for U1 (x=-d/2) and U2 (x=+d/2) to put the null at theta_null (xz plane).
%   Null where k d sin(theta) = phi1 - phi2; both shifters used symmetrically about 'mid'.
if nargin<3, mid = 0; end
k = 2*pi*f/299792458; d = 25e-3;
dphi = k*d*sind(theta_null_deg)*180/pi;
ph = [mid + dphi/2, mid - dphi/2];
end
