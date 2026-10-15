function toy = mtsf_toy_array(Nx, Ny, d, f, ang, Rself, Xself)
%MTSF_TOY_ARRAY  Analytic stand-in for the HFSS data so the whole flow runs without a solver.
%   Nx x Ny array of x-directed short electric dipoles (E-plane = phi 0, like the paper's cell), period d (m), frequency f (Hz).
%   Z_mn from the free-space dyadic Green's function (exact for point dipoles), element patterns
%   from the same model, so Re{Z} = (1/eta) <F_m,F_n> holds (checked in mtsf_selftest).
%   Replace toy.Z / toy.F with your HFSS Touchstone + embedded patterns for the real design.
if nargin<6, Rself = 50; end
if nargin<7, Xself = 0; end
c0 = 299792458; eta = 376.730313; k = 2*pi*f/c0;
l  = sqrt(Rself*6*pi/eta)/k;                         % dipole length giving R_self
[ix,iy] = ndgrid(1:Nx,1:Ny);
xy = [(ix(:)-(Nx+1)/2)*d, ((Ny+1)/2-iy(:))*d];       % index m = (col,row) column-major, row 1 at top
M  = size(xy,1);
Z  = zeros(M);
for m = 1:M
    for n = 1:M
        if m == n, Z(m,n) = Rself + 1j*Xself; continue; end
        R = norm(xy(m,:)-xy(n,:)); cpsi = (xy(m,1)-xy(n,1))/R;     % x_hat . R_hat
        kr = k*R;
        A = 1 + 1/(1j*kr) - 1/kr^2;  B = 1 + 3/(1j*kr) - 3/kr^2;
        Z(m,n) = (1j*eta*k*l^2/(4*pi)) * exp(-1j*kr)/R * (A - B*cpsi^2);
    end
end
ph  = exp(1j*k*(ang.dirx*xy(:,1).' + ang.diry*xy(:,2).'));          % e^{+j k r_hat . r_m}
cst = -1j*eta*k*l/(4*pi);
Eth = cst*(cos(ang.theta).*cos(ang.phi)).*ph;     % x_hat . theta_hat
Eph = -cst*(sin(ang.phi)).*ph;                    % x_hat . phi_hat
toy.Z = Z; toy.F = [Eth; Eph]; toy.xy = xy; toy.k0 = k; toy.l = l; toy.eta = eta;
toy.elem.Eth = cst*cos(ang.theta).*cos(ang.phi); toy.elem.Eph = -cst*sin(ang.phi);
toy.rc = [iy(:), ix(:)];                               % [row col] of each port index
end
