function [t, u] = ns_cut(Et, Ep, TH, PH, phi_deg)
%NS_CUT  Normalised dB cut (theta -180..180) in the plane phi.
php = mod(phi_deg,360); phm = mod(phi_deg+180,360); phv = PH(1,:)*180/pi;
[~,i1] = min(abs(phv-php)); [~,i2] = min(abs(phv-phm));
th = TH(:,1)*180/pi; U = abs(Et).^2 + abs(Ep).^2;
t = [-flipud(th); th(2:end)]; u = [flipud(U(:,i2)); U(2:end,i1)];
u = 10*log10(u/max(u) + 1e-12);
end
