%MTSF_DESIGN_FROM_HFSS  Real-data version of the paper's flow (Sec. IV-C, steps 1-6).
%  Inputs you produce in HFSS (see 06_docs/DESIGN_GUIDE.md, section 6):
%    1) metasurface_121port.s121p  - all 121 lumped ports, 50-ohm reference, design frequency only
%    2) ff/port_###.csv            - embedded far field of each port (others terminated in 50 ohm)
%    3) (reflective only) ff/scat_open.csv - scattered field with every port OPEN for the plane wave
%  Output: optimised reactances -> X csv for build_dxf.py, lumped L/C table, stub lengths, S-params.
clear;
%% ---------------- user settings ----------------
f0      = 10e9;
design  = 'I';            % 'I' (beam), 'II' (flat-top), 'III' (MIMO), 'IV' (splitter), 'V' (2-plane-wave)
snp     = 'metasurface_121port.s121p';
ffdir   = 'ff';
dth = 2; dph = 4;          % must match the HFSS infinite-sphere export
Nc = 11; M = Nc^2; d = 5.7e-3;
Xmin = -150; Xmax = 150;   % realisable reactance range (meander stubs in a lambda/5 cell)
%% ---------------- step 1: network data ----------------
[Z, ~, fz] = mtsf_read_touchstone(snp, f0);
fprintf('Z-matrix at %.3f GHz, %dx%d\n', fz/1e9, size(Z,1), size(Z,2));
[Fh, ang] = mtsf_load_hfss_patterns(ffdir, M, dth, dph, 180);
F  = mtsf_embedded_to_open(Fh, Z, 50);        % 50-ohm-terminated -> current basis (1 A, others open)
k0 = 2*pi*f0/299792458;
[ci, ri] = meshgrid(1:Nc,1:Nc); rc = [reshape(ri.',[],1), reshape(ci.',[],1)];  % m=(r-1)*11+c
xy = [(rc(:,2)-6)*d, (6-rc(:,1))*d];
idx = @(r,c) (r-1)*Nc + c;
front = ang.theta <= pi/2;  w = ang.w.*front;  % fit the front hemisphere (ground-backed surface)
%% ---------------- step 2: desired pattern & states ----------------
blank = struct('Vexc',[],'E0',[],'sgn',1,'type','match','Edes',[],'IE',[],'main',[],'side',[],'sll_dB',[],'wside',[]);
switch design
  case {'I','II'}
    iE = idx(6,6); iL = setdiff(1:M,iE); st = blank;
    st.Vexc = -Z(iL,iE); st.E0 = F(:,iE); st.IE = 1;
    if strcmp(design,'I'), st.Edes = mtsf_desired_pattern(ang, xy, k0, [-30 0], 'magdipole');
    else, st.type = 'mask'; st.main = ang.theta<=20*pi/180; st.side = ang.theta>=40*pi/180 & front;
          st.sll_dB = -13; st.wside = 3; end
    beta = 0.3; gamma = 0;
  case 'III'
    iE = [idx(6,4) idx(6,8)]; iL = setdiff(1:M,iE);
    thn = mtsf_orthogonal_beams([-1 1], Nc*d, k0);
    for k = 1:2
        st(k) = blank; IE = zeros(2,1); IE(k) = 1;
        st(k).Vexc = -Z(iL,iE)*IE; st(k).E0 = F(:,iE)*IE; st(k).IE = IE;
        st(k).Edes = mtsf_desired_pattern(ang, xy, k0, [thn(k) 90], 'magdipole');   % H-plane beams
    end
    beta = 0.3; gamma = 0.3;
  case {'IV','V'}
    iE = []; iL = 1:M;
    S0 = dlmread(fullfile(ffdir,'scat_open.csv'), ',', 1, 0);   % same column format, open ports
    Es = [S0(:,3)+1j*S0(:,4); S0(:,5)+1j*S0(:,6)];
    st = blank; st.sgn = -1; st.E0 = Es;
    st.Vexc = mtsf_voc_planewave(F, ang, 30, 0, 'theta', k0);
    st.Edes = mtsf_desired_pattern(ang, xy, k0, [30 90; -30 90], 'magdipole');
    if strcmp(design,'V')   % second incidence -> second state (needs scat_open_2.csv)
        S1 = dlmread(fullfile(ffdir,'scat_open_2.csv'), ',', 1, 0);
        st(1).Edes = mtsf_desired_pattern(ang, xy, k0, [-30 90], 'magdipole');
        st(2) = st(1); st(2).E0 = [S1(:,3)+1j*S1(:,4); S1(:,5)+1j*S1(:,6)];
        st(2).Vexc = mtsf_voc_planewave(F, ang, 30, 90, 'phi', k0);
        st(2).Edes = mtsf_desired_pattern(ang, xy, k0, [-30 0], 'magdipole');
    end
    beta = 0; gamma = 0;
end
prob = struct('Z',Z,'iL',iL,'iE',iE,'F',F,'w',w,'Z0',50,'alpha',1,'beta',beta,'gamma',gamma,'states',st);
%% ---------------- steps 3-5: currents eq.(8) -> complex loads eq.(5) -> reactive seed ----------------
[X0, ZLc] = mtsf_seed(prob);
fprintf('Complex loads: Re %.0f..%.0f ohm (discarded), Im %.0f..%.0f ohm\n', min(real(ZLc(:))), max(real(ZLc(:))), min(imag(ZLc(:))), max(imag(ZLc(:))));
%% ---------------- step 6: optimise eq.(11) ----------------
[X, info] = mtsf_multistart(prob, X0, Xmin*ones(numel(iL),1), Xmax*ones(numel(iL),1), 6, 2000);
[J, ~, out] = mtsf_cost(X, prob);
if ~isempty(iE), S = mtsf_reduced_S(Z, iL, iE, X, 50); disp('S at feeds (dB):'); disp(20*log10(abs(S))); end
%% ---------------- outputs ----------------
Xg = nan(Nc); for n = 1:numel(iL), Xg(rc(iL(n),1), rc(iL(n),2)) = X(n); end
mtsf_write_X_csv(Xg, sprintf('design%s_X_optimised.csv', design));
T = mtsf_X_to_LC(X, f0); Ls = mtsf_X_to_stub(X, f0);
fid = fopen(sprintf('design%s_loads.csv',design),'w');
fprintf(fid,'row,col,X_ohm,type,L_nH,C_pF,stub_mm_first_guess\n');
for n = 1:numel(iL)
    fprintf(fid,'%d,%d,%.2f,%s,%.4f,%.4f,%.3f\n', rc(iL(n),1), rc(iL(n),2), X(n), T.type(n), T.L_nH(n), T.C_pF(n), Ls(n));
end
fclose(fid);
for s = 1:numel(st)
    if strcmp(st(s).type,'match'), mtsf_plot_cut(ang, out.E{s}, st(s).Edes, 0, sprintf('Design %s state %d, \\phi=0',design,s));
                                   mtsf_plot_cut(ang, out.E{s}, st(s).Edes, 90, sprintf('Design %s state %d, \\phi=90',design,s)); end
end
fprintf('Done. Next: python 05_python_tools/build_dxf.py realise design%s_X_optimised.csv out.dxf --feeds ...\n', design);
