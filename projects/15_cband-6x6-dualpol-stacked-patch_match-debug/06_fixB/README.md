# 06_fixB: option 2 (wider feed start), evaluated and NOT recommended

`IN2_CU_fixB.dxf`: every element feed starts with 4.09 mm x 1.93 mm, then 2.00 mm x 6.37 mm along the drawn route,
then the existing 0.73 mm line (built by `02_openems/fix_feeds.py` from `03_results/fixb_design.txt`; layout checks in
`fixB_check.txt`). `F_CU_fixB.dxf` and `GND.dxf` are the supplied files unchanged.

Full-wave check (`sim_element_fix.py`, `03_results/opt2_summary.txt`): worst VSWR over 5.1-6.2 GHz H feed 3.50 -> 3.67,
V feed 3.59 -> 3.58. No improvement, so the board should not be changed this way. Kept as the record of the study.
