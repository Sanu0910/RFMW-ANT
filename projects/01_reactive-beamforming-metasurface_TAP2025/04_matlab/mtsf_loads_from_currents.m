function ZL = mtsf_loads_from_currents(Zll, IL, Vexc)
%MTSF_LOADS_FROM_CURRENTS  Complex loads that enforce currents IL, eq.(5):
%   Z_L = (V_exc - Z_LL I_L) ./ I_L        (Hadamard division)
%   Directly fed:  V_exc = -Z_LE * I_E        (eq.4)
%   Reflective:    V_exc = v_oc  (open-circuit voltage from the incident wave, eq.19)
%   Real part > 0 = loss, < 0 = gain -> discarded; Im part seeds the optimiser.
ZL = (Vexc - Zll*IL) ./ IL;
end
