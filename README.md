# WO240128A 3D viewer

Interactive 3D model of the Winstar WO240128A (240 × 128 COG graphic LCD, UC1608),
transcribed from the outline drawing. Same parameter set as the OpenSCAD model, so the
two stay in step.

## Open it

- `index.html` — works offline, loads `vendor/three.min.js`. Double-click it, or serve the
  folder (`python3 -m http.server`) and open it on the phone over the LAN.
- `wo240128a-3d.single.html` — one file, loads three.js from cdnjs. Handy to drop on any
  static host.

Fonts come from Google Fonts when online and fall back to system fonts otherwise.

## GitHub Pages

`.github/workflows/pages.yml` rebuilds the pages from `src/` on every push to `main` and
deploys `index.html` (plus `vendor/`, `assets/`, `exports/`, `scad/`) to GitHub Pages.
One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

## Branding

The page chrome uses the PerchWerks light / dark palette and Archivo from
[`perchwerks-style`](https://github.com/TheAngryRaven/perchwerks-style); the lockup SVG
is inlined from `brand/logos/perchwerks-lockup-duotone.svg`. The 3D-scene colours
(`--va`, `--aa`) are kept as drawing colours, not brand colours.

## Layout

```
index.html                   built page, offline (uses vendor/three.min.js)
wo240128a-3d.single.html     built page, single file (three.js from cdnjs)
src/viewer.template.html     the viewer source: CSS, markup, the 1-bit UI core, the three.js scene
src/build.py                 fills the placeholders and writes the pages above
src/make_logo.py             logo PNG → packed 1-bit bitmaps (writes src/logo_bitmaps.js)
src/logo_bitmaps.js          generated: LOGO_SRC at 240, 120 and 26 px wide
assets/logo.png              the logo the bitmaps were made from
scad/WO240128A_240x128_COG.scad   the OpenSCAD model (also embedded in the page)
vendor/three.min.js          three.js r128 (MIT)
exports/wo240128a.stl        full model, from OpenSCAD
exports/footprint.dxf        PCB-plane hole pattern (mode = "footprint")
exports/bezel.dxf            glass / VA / AA outlines (mode = "bezel")
```

Rebuild after editing the template, the .scad or the logo:

```
python3 src/make_logo.py assets/logo.png > src/logo_bitmaps.js   # only if the logo changed
python3 src/build.py
```

## The UI core (the part that becomes firmware)

Everything between `1-bit UI core` and `3D` in the template is written the way the C
version will be, with no browser APIs beyond `Math`:

- **Framebuffer** `fb` (240 × 128, one byte per dot, 1 = dark) with a clip rectangle.
  Primitives: `fbClear`, `fbPx`, `fbFill`, `fbRect`, `fbInvert`, `fbDither` (25 % / 50 %),
  `fbBlit` (bitmap, pixels become a value), `fbBlitXform` (scale + rotate by inverse
  mapping; `v = 2` inverts, used for the logo over the header bar).
- **Fonts**: `F57` is a 5 × 7 column-major bitmap font (`text57` draws at 1× or 2×);
  `segChar` / `segText` draw a seven-segment digit at any height from overlapping
  rectangles with rounded corners, `segTextRoll` does the odometer roll.
- **Timing**: `ease.*`, `tw(t0, dur, now, fn)`, `hash2` for dissolves, `mulberry32` seeded RNG.
  Every animation takes `now` in ms; nothing counts frames.
- **Session sim** `sim` + `simStep`: a direct-drive kart lap with corners, three sectors,
  session bests, delta vs best. `endSector` / `endLap` push events into `fx`.
- **Screen**: `drawHeader`, `drawBigTime`, `drawSpeedDelta`, `drawRpm`, `drawStatus`,
  `drawFx` (purple badge + sparkles, sector fill, best-lap banner), `postFx` (strobe,
  shake), `renderBoot` (spin-in, name, fly-to-header, gauge sweep, dissolve).
- **Scheduler**: `uiTick(step)` is called a fixed number of times per second from the
  page loop; `updateLcd` then models the FSTN response per displayed frame.

To port: keep the primitives' signatures, swap the row-major buffer for the UC1608 page
layout inside `fbFill`/`fbPx`, and emit `F57` and `LOGO_SRC` as `const uint8_t[]`.

## Where things are in the template

- `const P = {...}` — every dimension, same names and values as the .scad. `D` holds the
  derived values (ledge Z, pin tips, AA centre). Change a number in both files, or script it.
- `box(x0,x1,y0,y1,z0,z1,material,edges)` — all solids are axis-aligned boxes built in the
  drawing's frame: X from the outline's left edge, Y from its bottom edge, Z from the glass
  front face (negative = into the module). `model.position` shifts the outline centre to the
  origin.
- Groups `G.frame`, `G.glass`, `G.pins`, `G.led`, `G.pegs`, `G.chip`, `G.tape`, `G.outlines`
  are what the part toggles switch. `moving.frame` and `moving.rear` are the exploded-view
  carriers (frame moves 1×, pins/pegs 2×, glass stays).
- The screen is three layers on the glass: a VA plane in the FSTN background colour, an
  AA plane carrying a 256 × 128 `DataTexture` (one texel per dot, nearest-filtered, 240
  columns used) and a repeating gap tile that draws the 0.025 mm space between dots.
  `updateLcd(dt)` fills the texture (and the Flat canvas) from `fb` through the FSTN
  response model. **This is the hook for a UI emulator**: anything that writes `fb`
  shows up on the module.
- The orbit control is the `pointerdown/move/up` + `wheel` block: one pointer orbits,
  two pinch-zoom and pan, keyboard arrows orbit when the canvas has focus. `VIEWS` holds
  the preset camera angles; `fitRadius()` frames the model for the current aspect.
- Theme colours are CSS tokens on `:root` (light) with dark overrides; `applyTheme()`
  copies the 3D-relevant ones (background, grid, edge, VA/AA) into the scene and re-runs
  on `prefers-color-scheme` changes or a `data-theme` attribute change.

## Feeding it a framebuffer from firmware

If the firmware keeps the frame in UC1608 page layout (240 columns × 16 pages, one byte
= 8 vertical pixels, bit 0 = top row of the page), unpack it into `fb` like this instead
of calling `renderFrame`:

```js
function unpackPages(buf /* Uint8Array(3840) */) {
  for (let page = 0; page < 16; page++)
    for (let col = 0; col < 240; col++) {
      const b = buf[page * 240 + col];
      for (let i = 0; i < 8; i++) fb[(page * 8 + i) * 240 + col] = (b >> i) & 1;
    }
}
```

`updateLcd` takes it from there.

## OpenSCAD model

`scad/WO240128A_240x128_COG.scad` — open in OpenSCAD 2021.01 or newer.

- `origin` — `"lb_center"` (default), `"aa_center"`, `"lb_corner"`, `"pin1"`
- `mode` — `"3d"`, `"footprint"` (PCB hole pattern, export DXF), `"bezel"` (window outlines)
- `explode` — pulls frame and pins apart along Z
- `show_dots` + `dot_step` — draw the dot matrix; `pixel(col,row)` places one dot
- `pin_pos(n)` — PCB-plane position of pin n

Frame: +X right, +Y up, +Z toward the viewer, glass front face at Z = 0. Pins and pegs
point to −Z. Dimensions marked `(est.)` in the file were scaled off the drawing rather
than dimensioned; everything that affects a PCB or bezel is from the drawing.

## Licence notes

three.js r128 is MIT (Copyright 2010-2021 Three.js Authors). The viewer and model
files are yours to use as you like.
