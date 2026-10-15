function [S11, S21, G] = ns_rtps(f, Ci, p)
%NS_RTPS  S-parameters of the phase shifter, paper eqs.(1)-(7), read as a reflection-type phase shifter:
%   S11 = Gamma (T^2 + K^2),  S21 = 2 Gamma T K,   T = sqrt(1-C^2)/D,  K = jC sin(th)/D,
%   D = sqrt(1-C^2) cos(th) + j sin(th),  th = beta_ef l.
%   Gamma = (Zin - Zcl)/(Zin + Zcl), eq.(3);  Zin = stub transform of the load, eq.(4);
%   load = DC block (Cb, ESL) in series with [varactor (Rp, Ci, Lp; eq.5) || bias choke (Lb with SRF)].
c0 = 299792458; w = 2*pi*f(:).';
Zv  = p.Rp + 1./(1j*w*Ci) + 1j*w*p.Lp;
ZL  = 1j*w*p.Lb + w*p.Lb/40;
if isfield(p,'Lb_srf') && ~isempty(p.Lb_srf), Cpar = 1/((2*pi*p.Lb_srf)^2*p.Lb); ZL = 1./(1./ZL + 1j*w*Cpar); end
if isfield(p,'Rbias') && ~isempty(p.Rbias), ZL = 1./(1/p.Rbias + 1j*w*0.05e-12); end   % resistor bias option
Zn  = 1./(1./Zv + 1./ZL);
Zl  = Zn + 1./(1j*w*p.Cb) + 1j*w*p.Cb_esl;
bl  = w*sqrt(p.eeff)/c0*p.lstub;
Zin = p.Zstub*(Zl + 1j*p.Zstub*tan(bl))./(p.Zstub + 1j*Zl.*tan(bl));
G   = (Zin - p.Zcl)./(Zin + p.Zcl);
th  = w*sqrt(p.eeff)/c0*p.lcpl; C = p.Ccpl; s = sqrt(1-C^2);
D   = s*cos(th) + 1j*sin(th); T = s./D; K = 1j*C*sin(th)./D;
S11 = G.*(T.^2 + K.^2);  S21 = 2*G.*T.*K;
end
