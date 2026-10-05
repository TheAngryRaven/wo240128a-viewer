# WO240128A — PCB handoff

Everything needed to lay out the display footprint and the LED / button positions on the
PerchWerks datalogger PCB. All units mm. Coordinates are the **front view = PCB top view**
(the module sits on the top side, pins through), origin at the **bottom-left corner of the
98.7 × 67.7 module outline**; the CSVs also give every point relative to **pin 1**.

| File | What |
| --- | --- |
| `WO240128A_pcb_handoff.pdf` | 5 sheets: dimensioned footprint · pin-row detail with recommended pads · LED + button placement (layout B) · 1:1 check print · notes |
| `WO240128A_COG.kicad_mod` | KiCad footprint for the module, origin at pin 1 (23 pads P1.27, A/K slots, 2 NPTH pegs, fab / courtyard / silk) |
| `WO240128A_pcb.dxf` | Layers OUTLINE, COURTYARD, PTH, NPTH, VA, AA, LEDS_B, LEDS_A, BUTTONS, TEXT — import as a placement reference |
| `holes.csv` | Every hole: position, drill, recommended pad |
| `leds_layout_B.csv` | 11 × WS2812B-2020, D1–D11 in data-chain order (current layout: 5 top + 3 + 3) |
| `leds_layout_A.csv` | Alternative layout: 7 top + 2 + 2 |
| `buttons.csv` | Suggested button centres between the side LEDs |

Also in the repo: `../scad/WO240128A_240x128_COG.scad` (OpenSCAD model; `mode = "footprint"` / `"bezel"`),
`../exports/` (STL of the module, footprint and bezel DXFs).

## What is fixed and what is ours

- **From the Winstar drawing:** outline 98.7 × 67.7 ±0.5, pin 1 at X 35.38, 23 pins at P1.27 on Y 1.225,
  A/K tabs at X 19.35 / 79.35 on Y 2.25, Ø1.5 pegs at X 1.83 / 96.87 on Y 2.25. Check against the
  datasheet revision you buy, including the pin-out.
- **Recommended by us:** drill and pad sizes (signal Ø0.65 / 1.0 × 1.6 oval, A/K slot 2.3 × 1.0 /
  3.0 × 1.6, pegs NPTH Ø1.6). Keep the centres, adjust sizes to the fab's rules.
- **Placeholders until the enclosure exists:** top LED row 3.0 above the outline, side columns
  5.0 out from it. The pitches (16.117 top, 22.39 sides = half the AA height) come from the design.

## Mechanical notes

- The body is a component keep-out on the top side; the glass front face is 5.7 above the PCB,
  so the LEDs (0.84 tall) sit ~4.9 below it — plan light pipes or a stepped bezel.
- Below the frame rear face: signal pins 5.2, A/K tabs 3.8, pegs 2.0 — trim or allow under a 1.6 PCB.
- LEDs: ~15 mA each at full white for 5 mA/colour 2020 parts (check yours), ~0.5–1 mA idle each;
  a load switch on the LED rail and a 3.3 → 5 V level shifter on DIN are worth having.

Regenerate after changing the model: `python3 src/make_handoff.py` (needs `pip install ezdxf reportlab`).
