function p = ns_params()
%NS_PARAMS  Default parameters of the varactor-tuned broadside-coupled phase shifter (paper Sec. III-A).
%  Values marked [ASSUMED] are not stated in the paper; see 05_docs/DESIGN_GUIDE.
h = 0.508; er = 3.55;
[w50, ee50] = ns_ms_width(50, h, er);
p.f0      = 6e9;
p.Zcl     = 50;            % characteristic impedance of the coupled patches [ASSUMED 50]
p.Ccpl    = 10^(-3/20);    % 3-dB backward coupler (voltage coupling factor)
p.eeff    = ee50;
p.lcpl    = 299792458/p.f0/sqrt(ee50)/4;   % 90 deg at f0
p.Zstub   = 50;            % [ASSUMED] stub width = 50-ohm line
p.lstub   = 9.4e-3;        % paper l_stub
p.Rp      = 2;             % varactor series resistance (paper)
p.Lp      = 0.35e-9;       % [ASSUMED] package + pad inductance; 0 reproduces the paper's "negligible Lp" (116 deg max)
p.Cb      = 39e-12;  p.Cb_esl = 0.4e-9;     % DC block (paper 39 pF) + 0402 ESL [ASSUMED]
p.Lb      = 100e-9;  p.Lb_srf = 1.5e9;      % bias choke (paper 100 nH) + typical 0402 SRF [ASSUMED]
p.Cmin    = 0.14e-12; p.Cmax = 1.7e-12;     % MAVR-000120-14110P range (paper)
p.w50     = w50;
end
