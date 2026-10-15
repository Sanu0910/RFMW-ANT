function mtsf_write_X_csv(Xg, fname)
%MTSF_WRITE_X_CSV  Write an 11x11 reactance grid Xg(row,col) (row 1 = top, NaN = fed cell) in the
%   format read by 05_python_tools/build_dxf.py  (y index 11..1 = rows 1..11, paper axis y up):
%   python build_dxf.py realise <fname> realized.dxf --feeds 6,6
fid = fopen(fname,'w');
fprintf(fid,'y_index\\x_index'); fprintf(fid,',%d',1:size(Xg,2)); fprintf(fid,'\n');
for r = 1:size(Xg,1)
    v = Xg(r,:); v(isnan(v)) = 0;
    fprintf(fid,'%d',size(Xg,1)+1-r); fprintf(fid,',%.2f',v); fprintf(fid,'\n');
end
fclose(fid);
end
