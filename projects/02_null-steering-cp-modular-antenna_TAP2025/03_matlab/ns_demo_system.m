%NS_DEMO_SYSTEM  1-D / 2-D null steering, frequency squint, steering limits, CP check, Monte Carlo.
clear;
[TH, PH] = ndgrid((0:0.5:180)*pi/180, (0:2:358)*pi/180);
p = ns_params(); p.Lb_srf = []; p.Cb_esl = 0;          % case B (Lp = 0.35 nH)
% ---- steering limits
for f = [5 6 7]*1e9
    [~, ph] = ns_phase_curve(f, p); rng = max(ph);
    fprintf('PS range %.0f deg @ %.0f GHz -> max null angle +-%.1f deg\n', rng, f/1e9, asind(min(1, rng*pi/180/(2*pi*f/299792458*25e-3))));
end
% ---- 1-D: null placement check and squint of a fixed bias
el = ns_system('1D');
for tn = [-40 -25 0 25 40]
    ph = ns_phases_1d(tn, 6e9); [Et,Ep] = ns_array_field(el, ph, 6e9, TH, PH);
    [t,u] = ns_cut(Et,Ep,TH,PH,0); m = abs(t-tn)<=3; [dd,i] = min(u(m)); tt = t(m);
    fprintf('1-D null %+3d deg: found at %+.1f deg, depth %.0f dB\n', tn, tt(i), -dd);
end
[~, d40] = ns_phases_1d(40, 6e9);
for f = [5 6 7]*1e9
    fprintf('Fixed 6-GHz bias for 40 deg -> null at %.1f deg @ %.0f GHz\n', asind(d40*pi/180/(2*pi*f/299792458*25e-3)), f/1e9);
end
% ---- 2-D feasibility
[~, ph6] = ns_phase_curve(6e9, p);
fprintf('2-D: |u0|+|v0| <= %.3f with a %.0f deg phase shifter at 6 GHz\n', max(ph6)*pi/180/(2*pi*6e9/299792458*25e-3), max(ph6));
% ---- CP check (broadside AR) for both wing-type assignments
for ty = {'ABBA','AABB'}
    el = ns_system('CP', ty{1}); [Et,Ep] = ns_array_field(el, [90 0 0 90], 6e9, TH(1,1), PH(1,1));
    [AR,El,Er] = ns_axial_ratio(Et,Ep);
    fprintf('CP %s, +90 on U1,U4: broadside |E| = %.2e, AR = %.2f dB, sense %s\n', ty{1}, abs(Et)+abs(Ep), AR, ns_ifelse(abs(El)>abs(Er),'LHCP','RHCP'));
end
% ---- Monte Carlo rejection at 25 deg
rand('seed',1); randn('seed',1); el = ns_system('1D'); ph0 = ns_phases_1d(25, 6e9);
[TH2, PH2] = ndgrid((0:0.25:180)*pi/180, [0 pi]);
for sa = [0 0.5 1]
    rj = zeros(1,200);
    for n = 1:200
        amp = 10.^(sa*randn(1,2)/20); ph = ph0 + 4*randn(1,2);
        [Et,Ep] = ns_array_field(el, ph, 6e9, TH2, PH2, amp); [t,u] = ns_cut(Et,Ep,TH2,PH2,0);
        [~,i] = min(abs(t-25)); rj(n) = -u(i);
    end
    s = sort(rj); fprintf('MC amp %.1f dB / phase 4 deg rms: rejection at 25 deg median %.1f dB, 10th pct %.1f dB\n', sa, median(rj), s(20));
end
