function ne = nfms_tm0(f, P)
% Exact TM0 effective permittivity of PEC | air h_air | TLY-5 h_diel | PEC (transverse resonance).
k0 = 2*pi*f/P.c0;
fn = @(n2) sqrt(max(n2*k0^2 - k0^2, 1e-30))*tanh(sqrt(max(n2*k0^2 - k0^2, 1e-30))*P.h_air) ...
         - sqrt(max(P.er*k0^2 - n2*k0^2, 1e-30))/P.er*tan(sqrt(max(P.er*k0^2 - n2*k0^2, 1e-30))*P.h_diel);
ne = fzero(fn, [1+1e-9, P.er-1e-9]);
end
