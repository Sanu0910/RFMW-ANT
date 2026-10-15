function E = rba_af(ph_deg, f, th, amp, taper90)
%RBA_AF  E-plane field of the 1x5 array, D = 4.5 mm.  ph_deg: 1x5 element phases (deg).
if nargin<4 || isempty(amp), amp = ones(1,5); end
if nargin<5, taper90 = 4; end
k = 2*pi*f/299792458; x = ((0:4)-2)*4.5e-3;
E = (exp(1j*k*sin(th(:))*x) * (amp(:).*exp(1j*ph_deg(:)*pi/180))) .* rba_elem(th(:), taper90);
end
