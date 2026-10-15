function g = rba_elem(th, taper90)
%RBA_ELEM  E-plane (xoz) field of the shorted quarter-wave patch element: dB = -taper90*(theta/90deg)^2.
%  Default taper90 = 4 dB, read from paper Fig.3(a). Replace by an HFSS embedded cut for verification.
if nargin<2, taper90 = 4; end
g = 10.^(-taper90*(th*180/pi/90).^2/20);
end
