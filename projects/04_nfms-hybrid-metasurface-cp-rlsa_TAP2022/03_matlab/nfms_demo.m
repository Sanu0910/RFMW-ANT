% NFMS demo: Table I, corrected inverse, cells, radial line, phase maps.  Writes matlab_check.csv for the
% Python cross-check (02_python/crosscheck_matlab.py).  Runs in MATLAB or GNU Octave.
P = nfms_params();
fprintf('lambda0 %.3f mm, p = k0 sin(theta0) = %.5f rad/mm\n', P.lam0, P.p);
psi2 = [30 60 90 120 150 180];
[th, ph] = nfms_beam(P.p, P.p, 0*psi2, psi2, P.k0);
disp('Table I (psi1 = 0): psi2, theta, phi'); disp([psi2' th' ph']);
[a1, a2] = nfms_inverse(th(1:5), ph(1:5), P.p, P.k0);
disp('corrected inverse recovers (psi1, psi2):'); disp([a1' a2']);
s1 = nfms_cell_type1(4.0, 3.7, P.f0, P); [~, t2max] = nfms_cell_type2(P.rmax, P.f0, P); [~, t20] = nfms_cell_type2(0, P.f0, P);
fprintf('Type II r=0 %.2f deg, r=3.4 %.2f deg\n', t20, t2max);
fprintf('Type I a4 b3.7: |S21| %.3f dB, wrapped phase %.2f deg\n', 20*log10(abs(s1)), angle(s1)*180/pi);
ne = nfms_tm0(P.f0, P); fprintf('TM0 eps_eff %.4f, lambda_g %.3f mm\n', ne, P.lam0/sqrt(ne));
[corr, grad, hm1, hm2] = nfms_phase_maps(P);
fprintf('cells in aperture %d, HM I mean phase %.3f\n', sum(~isnan(hm1(:))), mean(hm1(~isnan(hm1))));
out = [th ph, a1 a2, 20*log10(abs(s1)) angle(s1)*180/pi t20 t2max ne sum(~isnan(hm1(:))) mean(hm1(~isnan(hm1))) mean(hm2(~isnan(hm2)))];
dlmwrite('matlab_check.csv', out, 'precision', '%.6f');
