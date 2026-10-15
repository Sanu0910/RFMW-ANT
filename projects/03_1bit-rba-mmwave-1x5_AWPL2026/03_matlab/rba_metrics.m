function [pk, sll, dB] = rba_metrics(E, th)
%RBA_METRICS  Peak angle (deg), side-lobe level (dB, highest local max outside the main lobe), normalised dB.
U = abs(E).^2; U = U/max(U); dB = 10*log10(U+1e-12);
[~, ip] = max(U); l = ip; r = ip;
while l>1 && U(l-1)<U(l), l = l-1; end
while r<numel(U) && U(r+1)<U(r), r = r+1; end
side = [dB(1:l-1); dB(r+1:end)]; if isempty(side), sll = -99; else, sll = max(side); end
pk = th(ip)*180/pi;
end
