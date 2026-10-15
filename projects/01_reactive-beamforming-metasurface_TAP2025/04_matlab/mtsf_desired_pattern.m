function Edes = mtsf_desired_pattern(ang, xy, k0, beams, elem)
%MTSF_DESIRED_PATTERN  Desired field, eq.(23): Edes = AF(theta,phi) * E_element(theta,phi).
%   beams : B x 2 [theta0 phi0] in deg (several rows -> multibeam, summed; e.g. beam splitter).
%   elem  : 'magdipole' (paper eq.22) or a struct with fields Eth, Eph (Na x 1).
%   Returns Edes as a stacked vector [Eth; Eph] (2Na x 1).
if nargin<5 || ischar(elem), [et,ep] = mtsf_magdipole_pattern(ang); else, et = elem.Eth; ep = elem.Eph; end
AF = zeros(numel(ang.theta),1);
for b = 1:size(beams,1)
    AF = AF + mtsf_array_factor(ang, xy, k0, beams(b,1), beams(b,2));
end
Edes = [AF.*et; AF.*ep];
end
