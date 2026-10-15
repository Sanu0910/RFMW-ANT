function th = mtsf_orthogonal_beams(n, w_aperture, k0)
%MTSF_ORTHOGONAL_BEAMS  Elevation angles of mutually orthogonal beams, eq.(25):
%   theta_n = asin(2 pi n / (w k0)).  For w = 2 lambda0, n = +-1 -> +-30 deg nominal
%   (paper quotes +-28.5 deg using the physical aperture 11*5.7 mm = 62.7 mm).
th = asind(2*pi*n./(w_aperture*k0));
end
