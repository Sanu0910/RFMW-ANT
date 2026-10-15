function el = ns_system(name, cptypes)
%NS_SYSTEM  Element positions r (m), polarisation p (world unit vector) and type sign s for '1D','2D','CP'.
%   Type A: s=+1; mirrored type B: s=-1 (the paper's built-in 180 deg).  Boards stand vertically, beam +z.
%   CP: cptypes = 'ABBA' (paper Fig.1(c) colours, U1..U4) or 'AABB' (co-phased opposite wings, recommended).
d = 25e-3;
switch upper(name)
  case '1D'
    el = struct('u',{1,2},'r',{[-d/2 0 0],[d/2 0 0]},'p',{[1 0 0],[1 0 0]},'s',{+1,-1});
  case '2D'
    el = struct('u',{1,2,3,4},'r',{[d/2 d/2 0],[-d/2 d/2 0],[d/2 -d/2 0],[-d/2 -d/2 0]}, ...
                'p',{[1 0 0],[1 0 0],[1 0 0],[1 0 0]},'s',{+1,-1,-1,+1});
  case 'CP'
    if nargin<2, cptypes = 'AABB'; end
    az = [45 135 315 225];                    % U1..U4 wing azimuths (U4 opposite U1, U3 opposite U2)
    for k = 1:4
        el(k).u = k; el(k).r = 12.5e-3*[cosd(az(k)) sind(az(k)) 0];
        el(k).p = [cosd(az(k)) sind(az(k)) 0];    % board x axis radially outward
        el(k).s = 1 - 2*(cptypes(k)=='B');
    end
end
end
