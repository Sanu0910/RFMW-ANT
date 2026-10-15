function s21 = nfms_cell_type1(a, b, f, P)
% S21 of a Type I cell (patches a, b, a, b on 3 x 1.6 mm TLY-5); ABCD cascade, capacitive patch grids.
eta0 = 376.730313668; eps0 = 8.8541878128e-12;
w = 2*pi*f*1e9; k = 2*pi*f/P.c0*sqrt(P.er); z = eta0/sqrt(P.er);
sz = [a b a b]; ee = [(1+P.er)/2 P.er P.er (1+P.er)/2];
M = eye(2);
for n = 1:4
  g = P.d - sz(n);
  if sz(n) <= 0, C = 0; else, C = P.Cscale*eps0*ee(n)*(2*P.d*1e-3/pi)*log(1/sin(pi*g/(2*P.d))); end
  M = M * [1 0; 1i*w*C 1];
  if n < 4, bt = k*P.tlam; M = M * [cos(bt) 1i*z*sin(bt); 1i*sin(bt)/z cos(bt)]; end
end
s21 = 2 / (M(1,1) + M(1,2)/eta0 + M(2,1)*eta0 + M(2,2));
end
