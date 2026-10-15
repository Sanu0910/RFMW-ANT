function [Et, Ep] = ns_array_field(el, ph_deg, f, TH, PH, amp, nexp, Eemb)
%NS_ARRAY_FIELD  Far field of the modular array.  Element: endfire printed dipole toward +z,
%   g(theta) = ((1+cos theta)/2)^nexp, E parallel to el(i).p.  Pass Eemb{i} = {Et_i, Ep_i}
%   (HFSS embedded patterns on the same grid) to replace the analytic element.
if nargin<6 || isempty(amp), amp = ones(1,numel(el)); end
if nargin<7 || isempty(nexp), nexp = 1.5; end
k = 2*pi*f/299792458;
st = sin(TH); ct = cos(TH); sp = sin(PH); cp = cos(PH);
rx = st.*cp; ry = st.*sp; rz = ct;
Et = zeros(size(TH)); Ep = Et;
for i = 1:numel(el)
    a  = el(i).s*amp(i)*exp(1j*ph_deg(i)*pi/180);
    af = exp(1j*k*(rx*el(i).r(1) + ry*el(i).r(2) + rz*el(i).r(3)));
    if nargin>=8 && ~isempty(Eemb)
        et = Eemb{i}{1}; ep = Eemb{i}{2};
    else
        g  = ((1+ct)/2).^nexp; pv = el(i).p;
        et = g.*(pv(1)*ct.*cp + pv(2)*ct.*sp - pv(3)*st);
        ep = g.*(-pv(1)*sp + pv(2)*cp);
    end
    Et = Et + a*af.*et; Ep = Ep + a*af.*ep;
end
end
