function AF = mtsf_array_factor(ang, xy, k0, th0_deg, ph0_deg, amp)
%MTSF_ARRAY_FACTOR  Array factor of eq.(21) with the progressive phase of eq.(24).
%   xy  : M x 2 element positions (m).  th0/ph0 : beam direction (deg, theta may be negative).
%   amp : optional M x 1 amplitude taper (default uniform).
%   Sign convention e^{+j k r_hat . r_m} for the pattern and e^{-j k u0 . r_m} for the
%   excitation, so the beam points to (th0,ph0) with e^{j w t} time dependence.
if nargin<6, amp = ones(size(xy,1),1); end
u0 = [sind(th0_deg)*cosd(ph0_deg), sind(th0_deg)*sind(ph0_deg)];
Iab = amp .* exp(-1j*k0*(xy*u0.'));                       % eq.(24) (sign: conjugate steering)
AF  = exp(1j*k0*(ang.dirx*xy(:,1).' + ang.diry*xy(:,2).')) * Iab;   % eq.(21)
end
