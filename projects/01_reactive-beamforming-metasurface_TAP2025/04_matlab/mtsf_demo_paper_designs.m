%MTSF_DEMO_PAPER_DESIGNS  End-to-end run of the paper's design flow on an analytic 11x11 toy array
%  (no HFSS needed).  Reproduces the *workflow* of Designs I, II, III and IV:
%     Step 1  impedance matrix + element patterns   (toy here; HFSS for the real board)
%     Step 2  desired pattern  eq.(21)-(23)
%     Step 3  port currents    eq.(8)
%     Step 4  complex loads    eq.(5)
%     Step 5  drop Re -> seed  eq.(9)
%     Step 6  optimise X       eq.(11)  (fmincon / Octave sqp, analytic gradient)
%  Numbers will differ from the paper because the toy element is a free-space dipole, not the
%  aperture-coupled cell. Swap in real data with mtsf_design_from_hfss.m.
clear; close all; rand('seed',1); randn('seed',1);
f  = 10e9; d = 5.7e-3; Nc = 11; M = Nc^2;
ang = mtsf_angle_grid(3, 6, 90);                   % front hemisphere
toy = mtsf_toy_array(Nc, Nc, d, f, ang, 50, 0);
idx = @(r,c) find(toy.rc(:,1)==r & toy.rc(:,2)==c);
lb = -300*ones(M,1); ub = 300*ones(M,1);
results = struct();

%% ---------------- Design I : directly fed, uniform aperture to (-30,0) ----------------
iE = idx(6,6); iL = setdiff(1:M, iE);
Edes = mtsf_desired_pattern(ang, toy.xy, toy.k0, [-30 0], toy.elem);
st = struct('Vexc',-toy.Z(iL,iE),'E0',toy.F(:,iE),'sgn',1,'type','match','Edes',Edes,'IE',1, ...
            'main',[],'side',[],'sll_dB',[],'wside',[]);
prob = struct('Z',toy.Z,'iL',iL,'iE',iE,'F',toy.F,'w',ang.w,'Z0',50,'alpha',1,'beta',0.05,'gamma',0,'states',st);
[X0, ZLc] = mtsf_seed(prob);
fprintf('\nDesign I seed: complex loads Re in [%.0f, %.0f] ohm (must be removed), Im in [%.0f, %.0f]\n', ...
        min(real(ZLc)),max(real(ZLc)),min(imag(ZLc)),max(imag(ZLc)));
[J0,~,o0] = mtsf_cost(X0, prob);
[X1, info] = mtsf_optimize(prob, X0, lb(iL), ub(iL), 2000);
[J1,~,o1] = mtsf_cost(X1, prob);
S = mtsf_reduced_S(toy.Z, iL, iE, X1, 50);
fprintf('Design I : pattern mismatch %.3f -> %.3f , S11 = %.1f dB  [%s]\n', o0.Jpat, o1.Jpat, 20*log10(abs(S)), info.solver);
results.I = struct('X',X1,'S11_dB',20*log10(abs(S)),'E',o1.E{1},'Edes',Edes,'iL',iL,'iE',iE);

%% ---------------- Design II : flat-top +-20 deg, SLL < -13 dB (mask) ----------------
mn = ang.theta <= 20*pi/180; sd = ang.theta >= 40*pi/180;
stm = st; stm.type = 'mask'; stm.main = mn; stm.side = sd; stm.sll_dB = -13; stm.wside = 3; stm.Edes = [];
sub = abs(toy.xy(:,1))<=1.01*d & abs(toy.xy(:,2))<=1.01*d;          % 3x3 sub-array: wide beam seed
AFw = exp(1j*toy.k0*(ang.dirx*toy.xy(sub,1).' + ang.diry*toy.xy(sub,2).'))*ones(nnz(sub),1);
sts = st; sts.Edes = [AFw.*toy.elem.Eth; AFw.*toy.elem.Eph];
pseed = prob; pseed.states = sts; X0 = mtsf_seed(pseed);
prob2 = prob; prob2.states = stm;
[X2, info] = mtsf_multistart(prob2, X0, lb(iL), ub(iL), 4, 800);
[~,~,o2] = mtsf_cost(X2, prob2); S = mtsf_reduced_S(toy.Z, iL, iE, X2, 50);
E = o2.E{1}; Na = numel(ang.w); U = abs(E(1:Na)).^2+abs(E(Na+1:end)).^2; U = U/mean(U(mn));
fprintf('Design II: ripple in +-20 deg = %.2f dB, worst sidelobe (>40 deg) = %.1f dB, S11 = %.1f dB\n', ...
        10*log10(max(U(mn))/min(U(mn))), 10*log10(max(U(sd))), 20*log10(abs(S)));
results.II = struct('X',X2,'U',U);

%% ---------------- Design III : MIMO, two feeds, orthogonal beams +-theta_n ----------------
thn = mtsf_orthogonal_beams([-1 1], Nc*d, toy.k0);
iE3 = [idx(6,4) idx(6,8)]; iL3 = setdiff(1:M, iE3);
for k = 1:2
    IE = zeros(2,1); IE(k) = 1;
    Ed = mtsf_desired_pattern(ang, toy.xy, toy.k0, [thn(k) 0], toy.elem);  % beams in the feed plane
    s3(k) = struct('Vexc',-toy.Z(iL3,iE3)*IE,'E0',toy.F(:,iE3)*IE,'sgn',1,'type','match','Edes',Ed,'IE',IE, ...
                   'main',[],'side',[],'sll_dB',[],'wside',[]);
end
prob3 = struct('Z',toy.Z,'iL',iL3,'iE',iE3,'F',toy.F,'w',ang.w,'Z0',50,'alpha',1,'beta',0.05,'gamma',0.1,'states',s3);
X0 = mtsf_seed(prob3);
[X3, info] = mtsf_multistart(prob3, X0, lb(iL3), ub(iL3), 4, 800);
[~,~,o3] = mtsf_cost(X3, prob3); S = mtsf_reduced_S(toy.Z, iL3, iE3, X3, 50);
fprintf('Design III: beams at %+.1f / %+.1f deg, mismatch %.3f / %.3f, S11 %.1f, S22 %.1f, S21 %.1f dB\n', ...
        thn(1), thn(2), o3.Jpat(1), o3.Jpat(2), 20*log10(abs(S(1,1))), 20*log10(abs(S(2,2))), 20*log10(abs(S(2,1))));
results.III = struct('X',X3,'S',S);

%% ---------------- Design IV : reflective beam splitter (30,0) -> (+-30, 90) ----------------
iL4 = 1:M;
voc = mtsf_voc_planewave(toy.F, ang, 30, 0, 'theta', toy.k0);
Ed4 = mtsf_desired_pattern(ang, toy.xy, toy.k0, [30 90; -30 90], toy.elem);
s4  = struct('Vexc',voc,'E0',zeros(size(Ed4)),'sgn',-1,'type','match','Edes',Ed4,'IE',[], ...
             'main',[],'side',[],'sll_dB',[],'wside',[]);
prob4 = struct('Z',toy.Z,'iL',iL4,'iE',[],'F',toy.F,'w',ang.w,'Z0',50,'alpha',1,'beta',0,'gamma',0,'states',s4);
X0 = mtsf_seed(prob4);
[X4, info] = mtsf_multistart(prob4, X0, lb, ub, 4, 800);
[~,~,o4] = mtsf_cost(X4, prob4);
fprintf('Design IV: reflected-pattern mismatch %.3f\n', o4.Jpat);
results.IV = struct('X',X4,'E',o4.E{1},'Edes',Ed4);

%% ---------------- realisation outputs ----------------
[Ls, mi] = mtsf_X_to_stub(results.I.X, f);
T = mtsf_X_to_LC(results.I.X, f);
fprintf('Realisation (Design I): stub lengths %.2f..%.2f mm (eps_eff %.2f, Zc %.1f ohm); lumped L up to %.2f nH, C down to %.3f pF\n', ...
        min(Ls), max(Ls), mi.eps_eff, mi.Zc, max(T.L_nH), min(T.C_pF));
Xg = nan(Nc); for n = 1:numel(iL), Xg(toy.rc(iL(n),1), toy.rc(iL(n),2)) = results.I.X(n); end
mtsf_write_X_csv(Xg, 'demo_designI_X.csv');
save('-v7','demo_results.mat','results');
try
    mtsf_plot_cut(ang, results.I.E, results.I.Edes, 0, 'Design I (toy): E-plane \phi=0');
    print('-dpng','-r110','demo_designI_cut.png');
    mtsf_plot_cut(ang, results.IV.E, results.IV.Edes, 90, 'Design IV (toy): H-plane \phi=90');
    print('-dpng','-r110','demo_designIV_cut.png');
catch err
    fprintf('(plots skipped: %s)\n', err.message);
end
