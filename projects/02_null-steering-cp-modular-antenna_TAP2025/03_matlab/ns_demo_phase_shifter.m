%NS_DEMO_PHASE_SHIFTER  Reproduce/inspect the phase-shifter claims (145 deg, +-2 deg, < 1 dB, 5-7 GHz).
clear; f = linspace(5e9,7e9,41);
cases = {'A ideal (Lp=0, ideal L/C)', 'B Lp=0.35 nH', 'C B + real 100nH/39pF', 'D B + 10k bias resistor'};
for k = 1:4
    p = ns_params(); p.Lb_srf = []; p.Cb_esl = 0;
    switch k
        case 1, p.Lp = 0;
        case 2, p.Lp = 0.35e-9;
        case 3, p.Lp = 0.35e-9; p.Lb_srf = 1.5e9; p.Cb_esl = 0.4e-9;
        case 4, p.Lp = 0.35e-9; p.Rbias = 10e3; p.Cb_esl = 0.4e-9;
    end
    Cs = logspace(log10(p.Cmin), log10(p.Cmax), 12); PH = zeros(12,numel(f)); IL = PH; RL = PH;
    for i = 1:12, [s11,s21] = ns_rtps(f, Cs(i), p); PH(i,:) = angle(s21); IL(i,:) = -20*log10(abs(s21)); RL(i,:) = -20*log10(abs(s11)); end
    PH = unwrap(PH,[],1)*180/pi; rel = PH - PH(end,:);
    imb = max(max(abs(rel - mean(rel,2))));
    fprintf('%-28s range %5.1f..%5.1f deg  imbalance +-%4.1f deg  IL<=%.2f dB  RL>=%.1f dB\n', cases{k}, ...
            min(abs(rel(1,:))), max(abs(rel(1,:))), imb, max(IL(:)), min(RL(:)));
end
fprintf('Single-varactor RTPS limit for C ratio %.1f: %.1f deg\n', 1.7/0.14, 4*atand(sqrt(1.7/0.14))-180);
