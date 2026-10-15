%RBA_DEMO  1-bit 1x5 RBA: beam table with the paper's preload, element-width sensitivity, squint, preload-error MC.
clear; f0 = 26.5e9; th = (-90:0.25:90)'*pi/180;
P = [55.78 -5.79 -73.37 0 -111.72];
paper = [0 -1 -8.25; 20 19 -5.23; -20 -21 -5.12; 40 38 -7.43; -40 -41 -6.72; 60 56 -4.69; -60 -54 -4.97];
fprintf('D = 4.5 mm = %.3f lambda0 at 26.5 GHz\n', 4.5e-3/(299792458/f0));
fprintf('target  code   peak(paper)    SLL(paper)\n');
codes = zeros(7,5);
for k = 1:7
    [b, pk, sll] = rba_best_state(paper(k,1), P, f0, -180, th); codes(k,:) = b;
    fprintf('%+4d   %d%d%d%d%d  %+6.1f (%+3d)  %6.2f (%6.2f)\n', paper(k,1), b, pk, paper(k,2), sll, paper(k,3));
end
for tp = [2 4 8 12]
    [~, pk] = rba_best_state(60, P, f0, -180, th, tp);
    fprintf('element taper %4.1f dB at 90 deg -> +60 beam at %+.1f deg\n', tp, pk);
end
for f = [25 26.5 28 29]*1e9
    [pk, sll] = rba_metrics(rba_af(P + codes(6,:)*-180, f, th), th);
    fprintf('+60 code at %.1f GHz -> peak %+.1f deg, SLL %.1f dB\n', f/1e9, pk, sll);
end
randn('seed', 7);
for sig = [0 5 10 15]
    w = [];
    for n = 1:100
        pre = P + sig*randn(1,5); S = -177 + 2*randn(1,5);
        for k = 1:7, [~, s] = rba_metrics(rba_af(pre + codes(k,:).*S, f0, th), th); w(end+1) = s; end
    end
    w = sort(w); fprintf('preload error %2d deg rms -> SLL 90th pct %.1f dB\n', sig, w(round(0.9*numel(w))));
end
