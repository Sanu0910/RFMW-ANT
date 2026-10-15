function [Cs, ph] = ns_phase_curve(f, p, n)
%NS_PHASE_CURVE  Relative S21 phase (deg, 0 at Cmax) vs capacitance at one frequency.
if nargin<3, n = 400; end
Cs = logspace(log10(p.Cmax), log10(p.Cmin), n); ph = zeros(1,n);
for k = 1:n, [~, s21] = ns_rtps(f, Cs(k), p); ph(k) = angle(s21); end
ph = unwrap(ph)*180/pi; ph = ph - ph(1);
end
