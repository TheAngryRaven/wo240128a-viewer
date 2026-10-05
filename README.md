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

## Actual size

**Actual size** (in the view chips) draws the module outline, glass, VA and the live AA at
physical millimetres. Browsers don't report real DPI (a CSS inch is always 96 px), so it
starts from an estimate by device class (phone 6.1, tablet 5.2, desktop 3.78 CSS px/mm)
and **Calibrate** matches a bank card (85.60 mm). The result is stored in `localStorage`
as device px per mm, keyed by the screen's device-pixel size, so desktop browser zoom
stays correct. Pinch-zoom on a phone breaks the scale; the bar says so.

## PCB handoff

`pcb-handoff/` is the package for the PCB engineer: a dimensioned PDF (footprint, pin-row detail,
LED + button placement, 1:1 check print, notes), a layered DXF, a KiCad footprint (origin pin 1)
and coordinate CSVs for the holes, both LED layouts and the buttons. `src/make_handoff.py`
regenerates it from the .scad (`pip install ezdxf reportlab`).

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
- **Theme C "Thermal"** (default): `drawTempC` (2× name, 32-px value, 14-px bar with band
  notches, peak flag, trend arrow, COLD / HIGH / HOT, whole-panel flip at warn), `drawLapC`
  (solid lap counter, 42-px digits, sector boxes; a new lap rolls in three steps),
  `updateRpmBarC` / `drawRpmBarC` (RPM bar: 18 slanted segments of 500 rpm from 6,000,
  stepping up in height; lit solid, unlit a stub, shift zone from 13,500 outlined, a peak
  cap that holds 0.7 s then falls a segment every 120 ms, 100 rpm of hysteresis, the band
  flips past 14,500; `RPMB` holds the numbers), `drawStatusC` (last lap and race clock only),
  `drawMidC` / `drawGripC` (grip loss: hazard-stripe wipe, skidding tyre, GRIP %, 6-block
  meter over the RPM bar, GRIP OK on recovery), `drawFxC` (sector and purple cards that open and close about the
  centre in three 80-ms steps, best-lap frames and card), `postFxC` (whole-screen flash, 2-px
  shake), `renderBootC` (logo fills with heat in six steps, flash, name, heat bar, shutters,
  gauge self-test). Drawn for the glass: no stroke under 2 px, motion that steps and holds,
  shown temperatures / RPM / grip held for 400 ms (`TH_HOLD`), alarms blinking at 1.25 Hz.
  `sim.race` is the race clock; `sim.grip` / `sim.gripLoss` stand in for the NPU's tyre model
  (the Grip loss toggle; Timekeeper and Pace ignore it).
- **Theme A "Timekeeper"**: `drawHeader`, `drawBigTime`, `drawSpeedDelta`, `drawRpm`,
  `drawStatus`, `drawFxA` (purple badge + sparkles, sector fill, best-lap banner),
  `postFxA` (strobe, shake), `renderBootA` (spin-in, name, fly-to-header, gauge sweep,
  dissolve).
- **Theme B "Pace"**: `drawLadder` (32-block RPM ladder with shift zone + peak),
  `drawGiantRpm`, `thermo`/`drawVitals` (EGT and water thermometers with target band,
  peak, over-temp blink), `drawPaceRow` (delta + trend + bar + speed), `drawLapStrip`,
  `drawIconRow` (8 × 8 `ICON` set + `battery`), `drawChip`, `drawFxB` (chips over the
  ladder, diagonal sweep, rings, checkered-flag wave, best-lap slam), `postFxB`
  (`glitchRows`), `renderBootB` (particle swarm, bouncing letters, `squeezeY` CRT
  collapse/expand, ladder self-test, slot-machine digits).
- **LEDs** (`LED`, `ledSetLayout`, `ledFrame`, `ledPace`, `ledFx`, `ledStatus`, `ledBoot`): 11 × WS2812 on
  the main PCB, in one of two layouts (`LED_LAYOUTS`): **B** "5 + 3 + 3" (default), the
  middle 5 of 7 top-row positions plus three down each side (AA top, middle, bottom), or
  **A** "7 + 2 + 2", all 7 on top plus two per side (AA middle, bottom). The chain runs up
  the left column, along the top row left to right, down the right column. `ledSetLayout`
  gives the UI core each LED's ring out from the centre (`LED_RING`; the side LEDs are the
  rings after the top row, top to bottom), its side (`LED_SIDE`) and X (`LED_X`, mm).
  `ledFrame(now)` runs at the end of every `renderFrame` and fills `LED.buf`, 33 bytes in
  WS2812 wire order (G, R, B), which is exactly what the firmware clocks out. Effects mix
  in perceptual 0..1 (`ledMix`); the conversion applies gamma 2.2 and then `LED.bright`.
  Roles: the **top row shows pace**, `LED.pace` = `'pip'` (default, the prototype: one pip,
  one LED per 0.25 s from the centre, right/green faster, left/red slower, 0.1 s of
  hysteresis, a 150-ms fading trail, the end pip blinks off the scale; `LED_POS` holds each
  top LED's signed step) or `'bar'` (`ledPaceBar`: grows out from the centre, the whole row
  = 0.6 s, glint while gaining, throb while losing); a slower sector (amber wipe) and an
  ordinary lap (white sweep) stay on the top row too. The **side columns are status LEDs**
  (`ledGrip`, `ledStatus`), dark unless: grip loss (amber breathing), overheat (red strobe
  on the hot gauge's side while it is over warn; EGT left, water right), rev limiter
  (`RPMB.over`, 14,500: the bottom LED each side flashes blue). **Purple sectors and best
  laps are global alerts** on every LED (purple wipe and twinkle; purple/white chase along
  the chain). Boot: a purple comet along the chain. Order per frame: pace, grip, events,
  then overheat and the limiter on top, so a warning is never hidden.
- `window.perchDemo` exposes `sim`, `fx`, `ui`, `fb`, `LED` and the event functions for poking
  from the console (`perchDemo.sim.bestLap = 70000` then press Lap forces a best lap).
- **Scheduler**: `uiTick(step)` is called a fixed number of times per second from the
  page loop; `updateLcd` then models the FSTN response per displayed frame.
- **Panel model** (`PANEL`, `panelTau`, `buildLut`, `updateLcd`): each dot is a first-order
  lag toward the framebuffer value, integrated exactly per displayed frame
  (`a = 1 − exp(−dt/τ)`). τ comes from the WO240128A-TFH datasheet's Tr 200 / Tf 250 ms
  typical (10–90 %, 25 °C) via τ = T / ln 9, scaled with temperature by an Arrhenius law
  (Ea/R = 3600 K, a textbook estimate, not a Winstar figure). Transmittance maps to colour
  through a 256-entry LUT mixed in linear light; "5:1 contrast" sets the dark state to the
  background at 1/CR luminance (datasheet CR 5 typ). Known simplifications: no dead time
  or S-curve in the optical response, no SPI / 64 Hz scan latency, uniform temperature
  across the panel. Fit τ on the bench with a photodiode or 240 fps phone video of a
  blinking block and replace the two constants.
- **The stat** is JavaScript time on the viewing device for the raster (`renderFrame`)
  and for the panel simulation; neither is a prediction for the nRF54.

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
- `LEDBAR` and `ledPoints` (next to `P`) place the LEDs. The top row uses 7 positions whose
  outer package edges are flush with the outline (the drawing's 98.7): pitch =
  (98.7 − 2.0) / 6 = 16.1167 mm for the 2020, 15.6167 for the 5050. Layout B fills the
  middle 5, so they bunch in the middle at the same pitch. The side columns sit `side`
  (5.0) out from the outline's sides, level with the AA's top / middle / bottom
  (`aaLevels`); `gap` (3.0, outline top edge → top row) and `side` are placeholders until
  the PCB exists. `LED_PKG` switches the 2020 (2.0 × 2.0 × 0.84, height from memory of its
  datasheet; check it) and the 5050 (5.0 × 5.0 × 1.6). The LEDs sit on the PCB plane (the
  frame's rear face) and are children of the scene rather than the module, so they stay
  put for the 6 o'clock mount, except that the side columns follow the AA, which rolls to
  the other half; they move with the pins in the exploded view. `ledLayout` places and
  scales the meshes and redraws the CAD-style dimensions (`dimension`, `buildLedDims`,
  toggled by "LED dimensions" in Show): the top-row pitch between positions 3 and 4, and each
  gap in the left column (where the buttons go). `ledShow` turns `LED.buf` into lens
  colour, a halo sprite, a glint sprite above ~86 % of the commanded level, and five point
  lights (thirds of the top row, one per side column). Actual size draws the same LEDs.

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
