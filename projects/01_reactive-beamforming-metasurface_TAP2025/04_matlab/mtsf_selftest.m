%MTSF_SELFTEST  Sanity checks: (1) power consistency Re{Z} vs pattern Gram matrix,
%   (2) analytic gradient of mtsf_cost vs finite differences (match, mask and S-terms).
clear; rng(1);
f = 10e9; d = 5.7e-3;
angF = mtsf_angle_grid(1.5, 3, 180);
toy = mtsf_toy_array(5, 5, d, f, angF);
G = toy.F' * ([angF.w;angF.w].*toy.F) / toy.eta;
err = norm(real(toy.Z) - real(G),'fro')/norm(real(toy.Z),'fro');
fprintf('Power check  ||Re Z - Gram/eta|| / ||Re Z|| = %.3e   (should be < 1e-2)\n', err);

ang = mtsf_angle_grid(5, 10, 90);
toy = mtsf_toy_array(5, 5, d, f, ang);
M = 25; iE = 13; iL = setdiff(1:M, iE);
prob = struct('Z',toy.Z,'iL',iL,'iE',iE,'F',toy.F,'w',ang.w,'Z0',50,'alpha',1,'beta',0.3,'gamma',0.2);
Edes = mtsf_desired_pattern(ang, toy.xy, toy.k0, [-30 0], toy.elem);
s1 = struct('Vexc',-toy.Z(iL,iE),'E0',toy.F(:,iE),'sgn',1,'type','match','Edes',Edes,'IE',1, ...
            'main',[],'side',[],'sll_dB',[],'wside',[]);
mn = ang.theta <= 20*pi/180; sd = ang.theta >= 40*pi/180;
s2 = struct('Vexc',-toy.Z(iL,iE),'E0',toy.F(:,iE),'sgn',1,'type','mask','Edes',[],'IE',1, ...
            'main',mn,'side',sd,'sll_dB',-13,'wside',2);
voc = mtsf_voc_planewave(toy.F(:,iL), ang, 30, 0, 'theta', toy.k0);
s3 = struct('Vexc',voc,'E0',zeros(size(Edes)),'sgn',-1,'type','match','Edes',Edes,'IE',[], ...
            'main',[],'side',[],'sll_dB',[],'wside',[]);
prob.states = [s1 s2 s3];
X = 40*randn(numel(iL),1);
[J,g] = mtsf_cost(X, prob);
h = 1e-4; gn = zeros(size(g));
for n = 1:numel(X)
    e = zeros(size(X)); e(n) = h;
    gn(n) = (mtsf_cost(X+e,prob) - mtsf_cost(X-e,prob))/(2*h);
end
fprintf('Gradient check  max|analytic-FD| / max|FD| = %.3e   (should be < 1e-4)\n', max(abs(g-gn))/max(abs(gn)));
% two-feed S-term gradient
iE2 = [12 14]; iL2 = setdiff(1:M,iE2);
p2 = prob; p2.iE = iE2; p2.iL = iL2;
p2.states = struct('Vexc',-toy.Z(iL2,iE2(1)),'E0',toy.F(:,iE2(1)),'sgn',1,'type','match','Edes',Edes,'IE',[1;0], ...
            'main',[],'side',[],'sll_dB',[],'wside',[]);
X = 40*randn(numel(iL2),1); [J,g] = mtsf_cost(X,p2); gn = zeros(size(g));
for n = 1:numel(X)
    e = zeros(size(X)); e(n) = h;
    gn(n) = (mtsf_cost(X+e,p2) - mtsf_cost(X-e,p2))/(2*h);
end
fprintf('Gradient check (2 feeds, S11/S22/S21) = %.3e\n', max(abs(g-gn))/max(abs(gn)));
% embedded (50-ohm terminated) -> open-circuit pattern conversion round trip
vs = 2*sqrt(2*50); Fh = toy.F/(toy.Z+50*eye(M))*vs;
fprintf('Embedded->open pattern conversion error %.2e\n', norm(mtsf_embedded_to_open(Fh,toy.Z,50,vs)-toy.F,'fro')/norm(toy.F,'fro'));
