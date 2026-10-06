#!/usr/bin/env python3
"""
STEP models for the WO240128A module and its PCB footprint / LED + button layout.

    python3 src/make_step.py        # needs: pip install cadquery ezdxf reportlab

Writes pcb-handoff/:
    WO240128A_display.step     the module (frame, glass, VA/AA, chip, 23 pins, A/K tabs, pegs). KiCad 3D-model frame:
                               origin = pin 1, +X right, +Y up (front view), Z = 0 = PCB top = frame rear face,
                               glass front at Z = +5.7, pins/tabs/pegs go to -Z through the board.
                               Drop it on WO240128A_COG.kicad_mod with offset 0 / rotation 0 / scale 1.
    WO240128A_footprint.step   the footprint and layout on a 1.6 mm reference board: every drill, top copper pads,
                               11 x WS2812B-2020 bodies, 4 button-centre markers, courtyard. Same frame as above.
    WO240128A_assembly.step    both together: the module seated on the reference board.
Numbers come from scad/WO240128A_240x128_COG.scad and the layout in src/make_handoff.py, so the three files, the PDF,
the DXF and the KiCad footprint always agree.
"""
import cadquery as cq
from make_handoff import P, OUT, ROOT, n_pins, LAYOUT_B, BUTTONS, PIN_DRILL, PIN_PAD, LED_SLOT, LED_PAD, PEG_DRILL, KEEPOUT, LED_SIZE

BOARD_T = 1.6        # reference board thickness (placeholder: use yours)
CU_T = 0.035         # top copper
LED_H = 0.84         # WS2812B-2020 body height
MARGIN = 3.0         # reference board margin around everything

total_t = P["lcd_t"] + P["lb_t"]               # 5.7: glass front -> frame rear
X0, Y0 = P["pin1_x"], P["pin_y"]               # pin 1 = origin
def at(x, y, z=0.0): return (x - X0, y - Y0, z)
def zc(z_scad): return z_scad + total_t        # .scad Z (0 = glass front) -> PCB Z (0 = frame rear face)

def box(x, y, z, w, h, t): return cq.Workplane("XY").box(w, h, t, centered=False).translate(at(x, y, z))
def cyl(x, y, z, d, h): return cq.Workplane("XY").circle(d / 2).extrude(h).translate(at(x, y, z))
def slot(x, y, z, w, h, t):                    # rounded slot along X, centred on x, y
    return cq.Workplane("XY").slot2D(w, h).extrude(t).translate(at(x, y, z))

COL = {k: cq.Color(*v) for k, v in {
    "frame": (0.93, 0.93, 0.90, 1), "glass": (0.62, 0.78, 0.70, 0.45), "va": (0.84, 0.88, 0.80, 1),
    "aa": (0.77, 0.83, 0.74, 1), "metal": (0.78, 0.78, 0.80, 1), "chip": (0.12, 0.12, 0.12, 1),
    "board": (0.10, 0.35, 0.18, 1), "copper": (0.85, 0.65, 0.25, 1), "led": (0.96, 0.96, 0.94, 1),
    "lens": (0.85, 0.90, 1.0, 1), "button": (0.85, 0.15, 0.15, 1), "court": (0.6, 0.6, 0.6, 1)}.items()}

# ---------------------------------------------------------------- the module
def display():
    lw, lh, wall = P["lb_w"], P["lb_h"], P["frame_wall"]
    lcd_x0, lcd_y0 = (lw - P["lcd_w"]) / 2, (lh - P["lcd_h"]) / 2
    plate_t = P["lcd_t"] / 2
    a = cq.Assembly(name="WO240128A")

    frame = box(0, lcd_y0, zc(-total_t), lw, lh - lcd_y0, total_t)
    frame = frame.cut(box(lcd_x0, lcd_y0 - 1, zc(-P["lcd_t"]), P["lcd_w"], P["lcd_h"] + 1, P["lcd_t"] + 1))
    yc = lh - P["notch_top"] - P["notch_len"] / 2                    # glue notches in both side walls
    for xw in (0, lw - wall):
        n = (cq.Workplane("XY").slot2D(P["notch_len"], wall, angle=90).extrude(P["notch_depth"] + 1)
             .translate(at(xw + wall / 2, yc, zc(-P["notch_depth"]))))
        frame = frame.cut(n)
    for x in (0, lw - P["foot_w"]):                                   # feet at the bottom corners
        frame = frame.union(box(x, 0, zc(-total_t), P["foot_w"], P["foot_h"] + 0.01, total_t))
    for x in (P["peg_x"], lw - P["peg_x"]):                           # pegs, chamfered tips
        peg = cyl(x, P["peg_y"], zc(-total_t) - P["peg_len"] + 0.3, P["peg_d"], P["peg_len"] - 0.3 + 0.01)
        tip = (cq.Workplane("XY").circle((P["peg_d"] - 0.3) / 2).workplane(offset=0.3).circle(P["peg_d"] / 2).loft()
               .translate(at(x, P["peg_y"], zc(-total_t) - P["peg_len"])))
        frame = frame.union(peg).union(tip)
    a.add(frame, name="frame", color=COL["frame"])

    rear = box(lcd_x0, lcd_y0, zc(-P["lcd_t"]), P["lcd_w"], P["lcd_h"], plate_t)
    front = box(lcd_x0, lcd_y0 + P["ledge_h"], zc(-plate_t), P["lcd_w"], P["lcd_h"] - P["ledge_h"], plate_t)
    a.add(rear, name="glass_rear", color=COL["glass"])
    a.add(front, name="glass_front", color=COL["glass"])
    a.add(box(P["va_x0"], P["va_y0"], zc(0), P["va_w"], P["va_h"], 0.01), name="viewing_area", color=COL["va"])
    a.add(box(P["aa_x0"], P["aa_y0"], zc(0.01), P["aa_w"], P["aa_h"], 0.01), name="active_area", color=COL["aa"])
    a.add(box(lw / 2 - P["chip_w"] / 2, P["chip_y"] - P["chip_h"] / 2, zc(-plate_t), P["chip_w"], P["chip_h"], P["chip_t"]),
          name="driver_UC1608", color=COL["chip"])

    pins = None
    tip_z = -(P["lcd_t"] + P["pin_len"])
    for k in range(n_pins):
        x = P["pin1_x"] + k * P["pin_pitch"]
        tab = box(x - P["pin_w"] / 2, lcd_y0, zc(-plate_t), P["pin_w"], P["pin_tab_h"], P["pin_t"])
        leg = box(x - P["pin_w"] / 2, P["pin_y"] - P["pin_t"] / 2, zc(tip_z), P["pin_w"], P["pin_t"], -tip_z - plate_t + P["pin_t"])
        p = tab.union(leg)
        pins = p if pins is None else pins.union(p)
    a.add(pins, name="pins_1-23", color=COL["metal"])
    led_tip = -(total_t + P["led_pin_len"])
    for nm, x in (("A", P["led_a_x"]), ("K", P["led_k_x"])):
        a.add(box(x - P["led_pin_w"] / 2, P["led_pin_y"] - P["led_pin_t"] / 2, zc(led_tip), P["led_pin_w"], P["led_pin_t"], P["led_pin_len"] + 1),
              name=f"backlight_{nm}", color=COL["metal"])
    return a

# ---------------------------------------------------------------- footprint + layout on a reference board
def extents():
    xs = [0, P["lb_w"]] + [x for _, _, x, _ in LAYOUT_B] + [x for _, x, _ in BUTTONS]
    ys = [0, P["lb_h"]] + [y for _, _, _, y in LAYOUT_B] + [y for _, _, y in BUTTONS]
    return min(xs) - LED_SIZE / 2 - MARGIN, min(ys) - LED_SIZE / 2 - MARGIN, max(xs) + LED_SIZE / 2 + MARGIN, max(ys) + LED_SIZE / 2 + MARGIN

def footprint(with_parts=True):
    a = cq.Assembly(name="WO240128A_footprint")
    x0, y0, x1, y1 = extents()
    board = box(x0, y0, -BOARD_T, x1 - x0, y1 - y0, BOARD_T)
    pads = None
    def add_pad(s):
        nonlocal pads; pads = s if pads is None else pads.union(s)
    for k in range(n_pins):
        x = P["pin1_x"] + k * P["pin_pitch"]
        board = board.cut(cyl(x, P["pin_y"], -BOARD_T - 1, PIN_DRILL, BOARD_T + 2))
        pad = (box(x - PIN_PAD[0] / 2, P["pin_y"] - PIN_PAD[1] / 2, 0, *PIN_PAD, CU_T) if k == 0 else
               cq.Workplane("XY").slot2D(PIN_PAD[1], PIN_PAD[0], angle=90).extrude(CU_T).translate(at(x, P["pin_y"])))
        add_pad(pad.cut(cyl(x, P["pin_y"], -1, PIN_DRILL, 2)))
    for x in (P["led_a_x"], P["led_k_x"]):
        board = board.cut(slot(x, P["led_pin_y"], -BOARD_T - 1, *LED_SLOT, BOARD_T + 2))
        add_pad(slot(x, P["led_pin_y"], 0, *LED_PAD, CU_T).cut(slot(x, P["led_pin_y"], -1, *LED_SLOT, 2)))
    for x in (P["peg_x"], P["lb_w"] - P["peg_x"]):
        board = board.cut(cyl(x, P["peg_y"], -BOARD_T - 1, PEG_DRILL, BOARD_T + 2))
    a.add(board, name="reference_board_1.6", color=COL["board"])
    a.add(pads, name="pads_top_cu", color=COL["copper"])
    k = KEEPOUT                                                       # courtyard as a 0.05 wire frame on the top
    court = box(-k, -k, CU_T, P["lb_w"] + 2 * k, P["lb_h"] + 2 * k, 0.01).cut(box(-k + 0.1, -k + 0.1, 0, P["lb_w"] + 2 * k - 0.2, P["lb_h"] + 2 * k - 0.2, 1))
    a.add(court, name="courtyard", color=COL["court"])
    if with_parts:
        s = LED_SIZE
        for d, _, x, y in LAYOUT_B:
            a.add(box(x - s / 2, y - s / 2, 0, s, s, LED_H - 0.05), name=f"{d}_WS2812B-2020", color=COL["led"])
            a.add(box(x - 0.7, y - 0.7, LED_H - 0.05, 1.4, 1.4, 0.05), name=f"{d}_lens", color=COL["lens"])
        for d, x, y in BUTTONS:
            a.add(cyl(x, y, 0, 1.0, 0.5), name=f"{d}_centre_marker", color=COL["button"])
    return a

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    disp = display()
    disp.export(str(OUT / "WO240128A_display.step"))
    footprint().export(str(OUT / "WO240128A_footprint.step"))
    asm = footprint(); asm.name = "WO240128A_assembly"; asm.add(display(), name="WO240128A")
    asm.export(str(OUT / "WO240128A_assembly.step"))
    for f in ("WO240128A_display.step", "WO240128A_footprint.step", "WO240128A_assembly.step"):
        print(f"wrote pcb-handoff/{f}  ({(OUT / f).stat().st_size / 1024:.0f} KB)")
