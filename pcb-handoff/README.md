# WO240128A — PCB handoff

Everything needed to lay out the display footprint and the LED / button positions on the
PerchWerks datalogger PCB. All units mm. Coordinates are the **front view = PCB top view**
(the module sits on the top side, pins through), origin at the **bottom-left corner of the
98.7 × 67.7 module outline**; the CSVs also give every point relative to **pin 1**.

| File | What |
| --- | --- |
| `WO240128A_pcb_handoff.pdf` | 5 sheets: dimensioned footprint · pin-row detail with recommended pads · LED + button placement (5 top + 3 + 3) · 1:1 check print · notes |
| `WO240128A_COG.kicad_mod` | KiCad footprint for the module, origin at pin 1 (23 pads P1.27, A/K slots, 2 NPTH pegs, fab / courtyard / silk) |
| `WO240128A_pcb.dxf` | Layers OUTLINE, COURTYARD, PTH, NPTH, VA, AA, LEDS, BUTTONS, TEXT — import as a placement reference |
| `WO240128A_display.step` | 3D model of the module. KiCad 3D-model frame: origin pin 1, Z = 0 at the PCB top (frame rear face), glass front at +5.7, pins to −5.2. Attach to the `.kicad_mod` with offset 0, rotation 0, scale 1 |
| `WO240128A_footprint.step` | The footprint on a 1.6 mm reference board: every drill, top copper pads, courtyard, 11 × WS2812B-2020 bodies, button-centre markers (same origin) |
| `WO240128A_assembly.step` | Both together: the module seated on the reference board, for enclosure / bezel work |
| `holes.csv` | Every hole: position, drill, recommended pad |
| `leds.csv` | 11 × WS2812B-2020, D1–D11 in data-chain order (confirmed layout: 5 top + 3 + 3) |
| `buttons.csv` | Suggested button centres between the side LEDs |

Also in the repo: `../scad/WO240128A_240x128_COG.scad` (OpenSCAD model; `mode = "footprint"` / `"bezel"`),
`../exports/` (STL of the module, footprint and bezel DXFs).

## What is fixed and what is ours

- **From the Winstar drawing:** outline 98.7 × 67.7 ±0.5, pin 1 at X 35.38, 23 pins at P1.27 on Y 1.225,
  A/K tabs at X 19.35 / 79.35 on Y 2.25, Ø1.5 pegs at X 1.83 / 96.87 on Y 2.25. Check against the
  datasheet revision you buy, including the pin-out.
- **Recommended by us:** drill and pad sizes (signal Ø0.65 / 1.0 × 1.6 oval, A/K slot 2.3 × 1.0 /
  3.0 × 1.6, pegs NPTH Ø1.6). Keep the centres, adjust sizes to the fab's rules.
- **Confirmed by us:** 5 LEDs on top, 3 LEDs + 2 buttons down each side; side LEDs and buttons
  5.5 out from the outline. Pitches: 16.117 top (5 centred on the 7-wide pitch), 22.39 sides (half the AA height).
- **Placeholder until the enclosure exists:** top LED row 3.0 above the outline.

## Mechanical notes

- The body is a component keep-out on the top side; the glass front face is 5.7 above the PCB,
  so the LEDs (0.84 tall) sit ~4.9 below it — plan light pipes or a stepped bezel.
- Below the frame rear face: signal pins 5.2, A/K tabs 3.8, pegs 2.0 — trim or allow under a 1.6 PCB.
- LEDs: ~15 mA each at full white for 5 mA/colour 2020 parts (check yours), ~0.5–1 mA idle each;
  a load switch on the LED rail and a 3.3 → 5 V level shifter on DIN are worth having.

Regenerate after changing the model: `python3 src/make_handoff.py` (needs `pip install ezdxf reportlab`), then
`python3 src/make_step.py` for the STEP files (also needs `pip install cadquery`).

In the STEP files the reference board outline and its 1.6 mm thickness are placeholders, and so are the button markers
(Ø1 centre dots: no switch part has been chosen). The display's pin-tab height, chip and A/K tab thickness are cosmetic, as in the .scad.
