function T = mtsf_X_to_LC(X, f)
%MTSF_X_TO_LC  Lumped element equivalent of each reactance at frequency f (Hz).
%   X>0 -> inductor L = X/w ;  X<0 -> capacitor C = -1/(w X).   Returns table-like struct.
w = 2*pi*f;
T.X = X(:); T.type = repmat('L',numel(X),1); T.type(X<0) = 'C';
T.L_nH = nan(numel(X),1); T.C_pF = nan(numel(X),1);
T.L_nH(X>=0) = X(X>=0)/w*1e9;
T.C_pF(X<0)  = -1./(w*X(X<0))*1e12;
end
