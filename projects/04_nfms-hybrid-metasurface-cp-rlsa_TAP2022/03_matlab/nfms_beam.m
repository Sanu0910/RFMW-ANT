function [theta, phi] = nfms_beam(p1, p2, psi1, psi2, k)
% Beam direction of two rotated gradient metasurfaces, paper eqs. (1)-(2) (atan2 for the quadrant). Degrees.
s = sqrt(max(p1.^2 + p2.^2 + 2*p1.*p2.*cosd(psi1 - psi2), 0)) ./ k;
theta = asind(min(s, 1));
phi = atan2d(p1.*sind(psi1) + p2.*sind(psi2), p1.*cosd(psi1) + p2.*cosd(psi2));
end
