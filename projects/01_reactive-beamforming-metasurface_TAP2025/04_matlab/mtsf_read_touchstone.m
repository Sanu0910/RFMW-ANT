function [Z, S, freq, Z0] = mtsf_read_touchstone(fname, f_target)
%MTSF_READ_TOUCHSTONE  Read an HFSS .sNp (Touchstone v1, RI/MA/DB, any unit, S/Z/Y) and return the
%   impedance matrix Z at the frequency closest to f_target (Hz).  121-port files are large: export
%   ONLY the design frequency from HFSS (Results > Solution Data > Export Matrix Data, or
%   pyAEDT export in 05_python_tools/hfss_build_and_export.py).
%   Z = Z0 (I + S)(I - S)^{-1}   (uniform real reference impedance Z0).
fid = fopen(fname,'r'); assert(fid>0, 'cannot open %s', fname);
[~,~,ext] = fileparts(fname); Np = sscanf(ext(3:end-1),'%d');
unit = 1e9; fmt = 'MA'; par = 'S'; Z0 = 50; nums = [];
while true
    ln = fgetl(fid); if ~ischar(ln), break; end
    ln = strtrim(ln); if isempty(ln), continue; end
    if ln(1)=='!', continue; end
    if ln(1)=='#'
        tok = upper(strsplit(ln(2:end)));  tok = tok(~cellfun(@isempty,tok));
        for k = 1:numel(tok)
            switch tok{k}
                case {'HZ'}, unit = 1; case {'KHZ'}, unit = 1e3; case {'MHZ'}, unit = 1e6; case {'GHZ'}, unit = 1e9;
                case {'S','Y','Z'}, par = tok{k};
                case {'RI','MA','DB'}, fmt = tok{k};
                case {'R'}, Z0 = str2double(tok{k+1});
            end
        end
        continue
    end
    c = strfind(ln,'!'); if ~isempty(c), ln = ln(1:c(1)-1); end
    nums = [nums; sscanf(ln,'%f')]; %#ok<AGROW>
end
fclose(fid);
per = 1 + 2*Np^2; nf = floor(numel(nums)/per);
D = reshape(nums(1:nf*per), per, nf);
freq = D(1,:)*unit;
if nargin<2, f_target = freq(1); end
[~,i] = min(abs(freq - f_target));
v = D(2:end,i); a = v(1:2:end); b = v(2:2:end);
switch fmt
    case 'RI', x = a + 1j*b;
    case 'MA', x = a.*exp(1j*b*pi/180);
    case 'DB', x = 10.^(a/20).*exp(1j*b*pi/180);
end
X = reshape(x, Np, Np).';           % Touchstone order: row-major (S11 S12 ... S1N, S21 ...)
if Np == 2, X = reshape(x,2,2); end  % 2-port files use S11 S21 S12 S22
I = eye(Np);
switch par
    case 'S', S = X; Z = Z0*(I+S)/(I-S);
    case 'Z', Z = X*Z0;       S = (Z/Z0 - I)/(Z/Z0 + I);    % Touchstone v1 Z/Y are normalised to R
    case 'Y', Z = inv(X/Z0);  S = (Z/Z0 - I)/(Z/Z0 + I);
end
freq = freq(i);
end
