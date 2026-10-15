# Logo for the lid engraving
Drop the logo here as **`BEL_logo.svg`**. Then run `python 02_python/build_enclosures.py`, and every lid is rebuilt with the logo engraved in place of the placeholder text "BEL".

- **Outlines only:** filled closed paths. Convert any text and strokes to paths first (Inkscape: Path → Object to Path, then Path → Stroke to Path).
- **viewBox:** set it. The builder scales the logo to `logo_w` = 26 mm wide (`encl_config.py`, `BOX["logo_w"]`).
- **Colours:** one colour is enough. Every closed shape is cut 0.3 mm deep.
- **Public repo:** this repository is public. Only commit the logo file if you're allowed to publish it; otherwise keep it local (`.gitignore` it).
