%MTSF_SELFTEST_TOUCHSTONE  Write a random 3-port S-matrix to .s3p and read it back.
S = (randn(3)+1j*randn(3))*0.2; S = (S+S.')/2;
fid = fopen('tmp_test.s3p','w'); fprintf(fid,'# GHz S RI R 50\n'); fprintf(fid,'10');
for r = 1:3, for c = 1:3, fprintf(fid,' %.12g %.12g', real(S(r,c)), imag(S(r,c))); end; fprintf(fid,'\n'); end
fclose(fid);
[Z,S2] = mtsf_read_touchstone('tmp_test.s3p', 10e9); delete('tmp_test.s3p');
fprintf('Touchstone round-trip error %.2e ; Z->S check %.2e\n', norm(S-S2), norm((Z/50-eye(3))/(Z/50+eye(3)) - S));
