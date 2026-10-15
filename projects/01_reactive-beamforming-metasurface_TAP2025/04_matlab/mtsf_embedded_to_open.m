function Fopen = mtsf_embedded_to_open(Fhfss, Z, Z0, vs)
%MTSF_EMBEDDED_TO_OPEN  Convert HFSS embedded element patterns (one port driven, all other ports
%   terminated in Z0, the HFSS default) into the CURRENT-BASIS patterns the paper uses
%   (port m carries 1 A, all other ports open-circuited).
%   Field is linear in port currents: E = Fopen * I.  With HFSS drive of port m:
%   I = (Z + Z0 I)^{-1} vs e_m  =>  Fhfss = Fopen (Z+Z0)^{-1} vs  =>  Fopen = Fhfss (Z+Z0) / vs
%   vs : source EMF used by HFSS for each port (same for all ports -> only a global scale,
%        which the optimiser's free complex scale absorbs).  For 1 W incident power,
%        vs = 2*sqrt(2*Z0) (peak) in the power-wave convention.
if nargin<3, Z0 = 50; end
if nargin<4, vs = 2*sqrt(2*Z0); end
M = size(Z,1);
Fopen = (Fhfss * (Z + Z0*eye(M))) / vs;
end
