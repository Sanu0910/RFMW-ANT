function [s21, ph_unwrapped] = nfms_cell_type2(r, f, P)
% Type II cell: TLY-5 slab h = 4.8 mm with an air hole of radius r; 2-D Maxwell Garnett permittivity.
eta0 = 376.730313668;
fr = pi*r^2/P.d^2; eh = P.er;
e = eh*((1+fr) + (1-fr)*eh) / ((1-fr) + (1+fr)*eh);
k = 2*pi*f/P.c0*sqrt(e); z = eta0/sqrt(e); bt = k*P.h;
s21 = 2 / (cos(bt) + 1i*z*sin(bt)/eta0 + 1i*sin(bt)/z*eta0 + cos(bt));
ph = angle(s21)*180/pi; ref = -bt*180/pi;
ph_unwrapped = ph + 360*round((ref - ph)/360);
end
