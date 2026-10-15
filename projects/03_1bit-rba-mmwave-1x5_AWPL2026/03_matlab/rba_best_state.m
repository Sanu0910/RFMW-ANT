function [b, pk, sll] = rba_best_state(theta0, preload, f, S, th, taper90)
%RBA_BEST_STATE  Exhaustive search over the 32 one-bit codes: maximise gain toward theta0 (with pointing penalty).
%  b(n)=0 -> SW1 ON (0 deg), b(n)=1 -> SW2 ON (S deg, ideally -180).
if nargin<4, S = -180; end
if nargin<5, th = (-90:0.25:90)'*pi/180; end
if nargin<6, taper90 = 4; end
[~, i0] = min(abs(th - theta0*pi/180)); best = -inf;
for c = 0:31
    bb = bitget(c, 5:-1:1);
    E = rba_af(preload + bb*S, f, th, [], taper90); [p, s, dB] = rba_metrics(E, th);
    score = dB(i0) + 20*log10(max(abs(E))) - 0.2*abs(p - theta0);
    if score > best, best = score; b = bb; pk = p; sll = s; end
end
end
