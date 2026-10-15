function [F, ang] = mtsf_load_hfss_patterns(folder, M, dth, dph, th_max)
%MTSF_LOAD_HFSS_PATTERNS  Load per-port embedded far fields exported by
%   05_python_tools/hfss_build_and_export.py (or manually from HFSS) as
%   folder/port_###.csv  with columns:  Theta_deg, Phi_deg, Re_rETheta, Im_rETheta, Re_rEPhi, Im_rEPhi
%   (one file per port, port index m = (row-1)*11 + col, rows top->bottom).  Returns F (2Na x M)
%   resampled on mtsf_angle_grid(dth,dph,th_max).  rE in volts (r*E with e^{-jkr} removed).
ang = mtsf_angle_grid(dth, dph, th_max);
Na = numel(ang.theta); F = zeros(2*Na, M);
for m = 1:M
    D = dlmread(fullfile(folder, sprintf('port_%03d.csv', m)), ',', 1, 0);
    th = D(:,1); ph = mod(D(:,2),360);
    et = D(:,3)+1j*D(:,4); ep = D(:,5)+1j*D(:,6);
    key  = round(th*100)*1e6 + round(ph*100);
    kq   = round(ang.theta*180/pi*100)*1e6 + round(ang.phi*180/pi*100);
    [ok, loc] = ismember(kq, key);
    assert(all(ok), 'port %d: export grid must contain the analysis grid (set HFSS sphere to %g/%g deg)', m, dth, dph);
    F(:,m) = [et(loc); ep(loc)];
end
end
