function voc = mtsf_voc_planewave(F, ang, th_i, ph_i, pol, k0, I0, E0)
%MTSF_VOC_PLANEWAVE  Open-circuit port voltages from an incident plane wave, eqs.(17)-(20).
%   v_oc = E_i . L_e,   L_e = j 4 pi r e^{j k r} / (k0 eta0 I0) * E_n(theta_i,phi_i)
%   F holds r*E (far-field, propagation phase removed), so the r e^{jkr} factor cancels.
%   pol: 'theta' or 'phi' (incident E-field polarisation).  E0: incident amplitude (V/m).
if nargin<7, I0 = 1; end
if nargin<8, E0 = 1; end
eta0 = 376.730313;
Na = numel(ang.theta);
[~, idx] = min( (ang.theta-th_i*pi/180).^2 + angle(exp(1j*(ang.phi-ph_i*pi/180))).^2 );
if strcmpi(pol,'theta'), row = idx; else, row = Na+idx; end
voc = (1j*4*pi/(k0*eta0*I0)) * E0 * F(row,:).';
end
