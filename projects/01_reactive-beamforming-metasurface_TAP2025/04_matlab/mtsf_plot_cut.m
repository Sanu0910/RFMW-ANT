function mtsf_plot_cut(ang, E, Edes, phi_cut_deg, ttl)
%MTSF_PLOT_CUT  Normalised dB cut (theta from -90 to 90) in the plane phi = phi_cut, as in Figs. 4c/8d.
Na = numel(ang.w);
U  = abs(E(1:Na)).^2 + abs(E(Na+1:end)).^2;
Ud = abs(Edes(1:Na)).^2 + abs(Edes(Na+1:end)).^2;
php = mod(phi_cut_deg,360)*pi/180; phm = mod(phi_cut_deg+180,360)*pi/180;
tol = 1e-6;
ip = find(abs(angle(exp(1j*(ang.phi-php))))<tol); im = find(abs(angle(exp(1j*(ang.phi-phm))))<tol);
th = [-ang.theta(im); ang.theta(ip)]*180/pi; u = [U(im); U(ip)]; ud = [Ud(im); Ud(ip)];
[th,o] = sort(th); u = u(o); ud = ud(o);
figure; plot(th,10*log10(ud/max(ud)),'b-','LineWidth',2); hold on;
plot(th,10*log10(u/max(u)),'k-','LineWidth',1.5); grid on; ylim([-40 0]); xlim([-90 90]);
xlabel('\theta (deg)'); ylabel('Normalized pattern (dB)'); legend('Desired','Network model (optimised)');
title(ttl);
end
