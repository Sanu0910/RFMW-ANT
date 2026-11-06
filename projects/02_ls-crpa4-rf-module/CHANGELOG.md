# Changelog: 02_ls-crpa4-rf-module

## 2026-11-05
- Project created. Customer Gerbers `Attachment_PR2600866273.zip` decoded (`read_interface.py`); interface CSVs,
  layer renders and `CRL-LS_design_basis.md` written; project 16 / 17 reference data and limiter data sheets copied in.

## 2026-11-05 (later)
- Full Ø200 mm board instead of a plug-in module (user): project 17 L channels + new NavIC S chains, hybrid
  FR-4/RO4350B stack-up, new footprints, BEL logo. DRC clean (8 accepted customer-hole courtyard notes); Gerbers/STEP exported.

## 2026-11-06
- NavIC S patches moved to lambda/2 spacing (60.15 mm, r 42.53 mm, user); S chains now run outward from the patch
  (outer feed pair, equal 5.064 mm feeds), last SAW + SMA turned onto the rim arc. Frame-via pitch 2.5 mm; S hybrid
  pin 2 tied to pin 5, ISO load outward. DRC 0 / 0.
- Combined L + S back cover CRL-LS-CRPA4-BC01 STEP (`covers.py`), fab package (`make_fab.py`: Gerber zip, CPL,
  IPC-D-356, BOM CSV/XLSX, fab notes), PCB STEP in the cover frame, renders.
- TA1442A and C2327J5003AHF data sheets in `00_vendor/`; both footprints rebuilt to the vendor land patterns
  (TA1442A 3.20 sq, 6 pads, GND vias in the pads; Xinger 0.35 x 0.33 pads, 0.65 pitch). RHCP hybrid wiring asserted.
  `+5V IN` legend moved off D1. DRC 0 / 0; fab package and BC01 regenerated.
- S patch part number CRL-LS-SP01 (BEL CRL in-house) in the BOM. Design review gap list saved
  (`05_docs/CRL-LS-CRPA4_design_review_gaps.md`). BC01 engraving: shorter 2nd line, S labels 2 mm further inward.
- RF budget / rejection / linearity / power (`rf_budget.py`, p16 Touchstone + board line lengths), drawing set
  `07_drawings/CRL-LS-CRPA4_DRAWINGS.pdf` (fab, array, assembly bottom/top, BC01, block diagram; `drawings.py`) and
  design report `05_docs/CRL-LS-CRPA4_design_report.md/.pdf` (`report.py`).
- Top side (L1) left without solder mask (user): board-wide F.Mask opening (board-only footprint MASKT, mask bridges
  allowed), so the L1 GND under the L and S patch bases is bare ENIG. Fab note 4 updated. DRC 0 / 0; Gerbers regenerated.
