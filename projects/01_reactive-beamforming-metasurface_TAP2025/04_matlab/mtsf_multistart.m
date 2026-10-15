function [Xb, info] = mtsf_multistart(prob, X0, lb, ub, nrand, maxit, spread)
%MTSF_MULTISTART  The reactive-load landscape is strongly multimodal (each cell's current phase is
%   limited to ~180 deg by a lossless load; full control relies on coupling, i.e. the evanescent
%   spectrum - Fig.5).  Run the analytic seed, an all-zero start and nrand random starts; keep the best.
if nargin<5, nrand = 6; end
if nargin<6, maxit = 2000; end
if nargin<7, spread = 100; end
starts = [X0(:), zeros(numel(X0),1), spread*(2*rand(numel(X0),nrand)-1)];
Jb = inf; Xb = X0(:); allJ = zeros(1,size(starts,2));
for s = 1:size(starts,2)
    [X, inf_] = mtsf_optimize(prob, starts(:,s), lb, ub, maxit);
    allJ(s) = inf_.J;
    if inf_.J < Jb, Jb = inf_.J; Xb = X; info = inf_; end
end
info.allJ = allJ;
fprintf('  multistart J per start: %s\n', sprintf('%.3f ', allJ));
end
