function [corr, grad, hm1, hm2, xc] = nfms_phase_maps(P)
% 48 x 48 phase maps (rows = y, columns = x), NaN outside the aperture; wrapped to (-360, 0].
xc = P.x0 + P.d*(0:P.N-1); rr = abs(xc(1:24));
w0 = @(p) -mod(360 - mod(p, 360), 360);
corr = NaN(P.N); grad = corr; hm1 = corr; hm2 = corr;
for i = 1:P.N
  for j = 1:P.N
    x = xc(i); y = xc(j); rho = hypot(x, y);
    if rho > P.Rcells + 1e-9, continue; end
    [~, kk] = min(abs(rho - rr));
    c = -P.fig12a(kk); g = w0(P.phi_first - P.dphi*(i-1));
    corr(j,i) = c; grad(j,i) = g; hm1(j,i) = w0(c + g); hm2(j,i) = g;
  end
end
end
