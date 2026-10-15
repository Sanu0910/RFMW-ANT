function [w, ee, z0] = ns_ms_width(Zt, h, er)
%NS_MS_WIDTH  Microstrip width (mm) for impedance Zt on height h (mm), Hammerstad. Also eps_eff, Z0.
lo = 0.05; hi = 10;
for k = 1:80
    w = (lo+hi)/2; [ee, z0] = ms(w, h, er);
    if z0 > Zt, lo = w; else, hi = w; end
end
end
function [ee, z0] = ms(w, h, er)
u = w/h; ee = (er+1)/2 + (er-1)/2*(1+12/u)^-0.5;
if u <= 1, z0 = 60/sqrt(ee)*log(8/u+u/4); else, z0 = 120*pi/(sqrt(ee)*(u+1.393+0.667*log(u+1.444))); end
end
