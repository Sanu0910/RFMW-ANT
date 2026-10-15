function ang = mtsf_angle_grid(dth_deg, dph_deg, th_max_deg)
%MTSF_ANGLE_GRID  Far-field sampling grid + quadrature weights.
%   ang = mtsf_angle_grid(2, 4, 90) -> theta 0..90 deg (front hemisphere), phi 0..360-dph.
%   Weights include sin(theta) dtheta dphi (solid angle). The paper writes the inner
%   product of eq.(7) as d(theta)d(phi) without sin(theta); using solid-angle weights makes
%   the Gram matrix proportional to the radiated-power matrix Re{Z} for a lossless array
%   and improves conditioning near the poles.  Set ang.w(:)=dth*dph to follow the paper literally.
if nargin<3, th_max_deg = 180; end
th = (0:dth_deg:th_max_deg)'*pi/180;
ph = (0:dph_deg:360-dph_deg)'*pi/180;
[TH,PH] = ndgrid(th,ph);
ang.theta = TH(:); ang.phi = PH(:);
dth = dth_deg*pi/180; dph = dph_deg*pi/180;
w = sin(ang.theta)*dth*dph;
w(ang.theta==0) = (dth/2)^2*pi/numel(ph);        % polar cap
ang.w = w; ang.nth = numel(th); ang.nph = numel(ph);
ang.dirx = sin(ang.theta).*cos(ang.phi);
ang.diry = sin(ang.theta).*sin(ang.phi);
ang.dirz = cos(ang.theta);
end
