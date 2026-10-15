function [psi1, psi2] = nfms_inverse(theta, phi, p, k)
% Rotation angles for a wanted beam (equal gradients p). CORRECTED form of paper eqs. (3)-(4):
% psi1,2 = phi +/- 0.5*acos((k sin(theta))^2 / (2 p^2) - 1). The printed form lacks the factor 2.
x = (k*sind(theta)).^2 ./ (2*p.^2) - 1;
x(abs(x) > 1) = NaN;
dl = acosd(x)/2; psi1 = phi + dl; psi2 = phi - dl;
end
