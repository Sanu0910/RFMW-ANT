function ph = ns_phases_2d(u0, v0, f)
%NS_PHASES_2D  Phases for the 2x2 system: null planes at u = u0 and v = v0.
%   phi_i = -(sx_i*ax + sy_i*ay),  ax = k d u0/2,  ay = k d v0/2;  element span = 2(|ax|+|ay|).
k = 2*pi*f/299792458; d = 25e-3;
ax = k*d*u0/2*180/pi; ay = k*d*v0/2*180/pi;
sx = [1 -1 1 -1]; sy = [1 1 -1 -1];
ph = -(sx*ax + sy*ay);
end
