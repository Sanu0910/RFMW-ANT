function P = nfms_params()
% Parameters of the NFMS RLSA + hybrid-metasurface system (Afzal, Esselle, Koli, IEEE TAP 70(1) 2022).
% Same values as 02_python/nfmsgeom.py and cells.py. Units mm, GHz.
P.c0 = 299.792458; P.f0 = 20; P.lam0 = P.c0 / P.f0; P.k0 = 2*pi/P.lam0;
P.er = 2.2; P.tlam = 1.6; P.h = 4.8; P.d = 7.5; P.rmax = 3.4; P.Cscale = 1.42;
P.theta0 = 19.5; P.dphi = 60; P.phi_first = -180; P.N = 48; P.x0 = -176.25; P.Rcells = 180;
P.h_air = 3.0; P.h_diel = 1.6;
P.fig12a = [74 35 161 106 119 118 129 117 110 102 98 111 91 109 97 104 84 90 54 65 49 20 -28 -8];
P.p = P.k0 * sind(P.theta0);
end
