function [AR, El, Er] = ns_axial_ratio(Et, Ep)
%NS_AXIAL_RATIO  Axial ratio (dB) and LHCP/RHCP components from theta/phi far-field components.
El = (Et + 1j*Ep)/sqrt(2); Er = (Et - 1j*Ep)/sqrt(2);
a = abs(El); b = abs(Er);
AR = 20*log10((a+b)./max(abs(a-b),1e-12));
end
