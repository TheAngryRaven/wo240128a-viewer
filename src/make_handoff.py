#!/usr/bin/env python3
"""
PCB handoff for the WO240128A module + the LED / button layout.

    python3 src/make_handoff.py        # needs: pip install ezdxf reportlab

Reads the module dimensions from scad/WO240128A_240x128_COG.scad (one source of truth) and writes pcb-handoff/:
    WO240128A_pcb_handoff.pdf   dimensioned drawings: footprint, pin-row detail, LED / button placement, 1:1 check, notes
    WO240128A_pcb.dxf           layers: OUTLINE, COURTYARD, PTH, NPTH, VA, AA, LEDS_B, LEDS_A, BUTTONS, TEXT (mm, LB corner)
    WO240128A_COG.kicad_mod     KiCad footprint, origin at pin 1
    holes.csv, leds_layout_B.csv, leds_layout_A.csv, buttons.csv
Frame: X right, Y up, origin at the bottom-left corner of the 98.7 x 67.7 outline, seen from the front (= the PCB's top side
when the module sits on it). The LED / button numbers come from the viewer (LEDBAR in src/viewer.template.html).
"""
import csv, math, pathlib, re
import ezdxf
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "pcb-handoff"
SCAD = ROOT / "scad" / "WO240128A_240x128_COG.scad"

# ---- module parameters straight from the .scad ----
P = {}
for m in re.finditer(r"(?<![a-z_0-9.])([a-z_][a-z_0-9]*)\s*=\s*(-?[0-9.]+)\s*;", SCAD.read_text()):
    P[m.group(1)] = float(m.group(2))
P["aa_y0"] = P["lb_h"] - P["aa_ytop"] - P["aa_h"]
P["va_y0"] = P["lb_h"] - P["va_ytop"] - P["va_h"]
P["aa_cy"] = P["aa_y0"] + P["aa_h"] / 2
n_pins = int(P["n_pins"])

# ---- PCB recommendations (not from the drawing) ----
PIN_DRILL, PIN_PAD = 0.65, (1.0, 1.6)        # 0.40 x 0.25 lead (diag 0.47); oval pad at 1.27 pitch leaves 0.27 copper gap
LED_SLOT, LED_PAD = (2.3, 1.0), (3.0, 1.6)   # 1.8 x 0.5 A/K tabs (slot as in the .scad)
PEG_DRILL = 1.6                              # NPTH for the dia 1.5 pegs
KEEPOUT = P["keepout"]

# ---- LED / button layout (viewer: LEDBAR, layout B default, WS2812B-2020) ----
LED_SIZE, LED_GAP, LED_SIDE, SLOTS = 2.0, 3.0, 5.0, 7
pitch = (P["lb_w"] - LED_SIZE) / (SLOTS - 1)
aa = {"top": P["aa_y0"] + P["aa_h"], "mid": P["aa_cy"], "bot": P["aa_y0"]}
def led_layout(top_slots, side_levels):
    pts = [("L", -LED_SIDE, aa[l]) for l in reversed(side_levels)]
    pts += [("T", LED_SIZE / 2 + k * pitch, P["lb_h"] + LED_GAP) for k in top_slots]
    pts += [("R", P["lb_w"] + LED_SIDE, aa[l]) for l in side_levels]
    return [(f"D{i+1}", s, x, y) for i, (s, x, y) in enumerate(pts)]   # chain order = DIN-to-DOUT order
LAYOUT_B = led_layout([1, 2, 3, 4, 5], ["top", "mid", "bot"])
LAYOUT_A = led_layout([0, 1, 2, 3, 4, 5, 6], ["mid", "bot"])
BUTTONS = [(f"SW{i+1}", x, (aa["top"] + aa["mid"]) / 2 if j == 0 else (aa["mid"] + aa["bot"]) / 2)
           for i, (x, j) in enumerate([(-LED_SIDE, 0), (-LED_SIDE, 1), (P["lb_w"] + LED_SIDE, 0), (P["lb_w"] + LED_SIDE, 1)])]
SIDE_CC = aa["top"] - aa["mid"]

def holes():
    h = [(f"{n}", "PTH", P["pin1_x"] + (n - 1) * P["pin_pitch"], P["pin_y"], f"dia {PIN_DRILL}", f"{PIN_PAD[0]} x {PIN_PAD[1]} oval" + (" (rect, pin 1)" if n == 1 else "")) for n in range(1, n_pins + 1)]
    h += [("A", "PTH slot", P["led_a_x"], P["led_pin_y"], f"{LED_SLOT[0]} x {LED_SLOT[1]}", f"{LED_PAD[0]} x {LED_PAD[1]} oval"),
          ("K", "PTH slot", P["led_k_x"], P["led_pin_y"], f"{LED_SLOT[0]} x {LED_SLOT[1]}", f"{LED_PAD[0]} x {LED_PAD[1]} oval"),
          ("PEG1", "NPTH", P["peg_x"], P["peg_y"], f"dia {PEG_DRILL}", "-"),
          ("PEG2", "NPTH", P["lb_w"] - P["peg_x"], P["peg_y"], f"dia {PEG_DRILL}", "-")]
    return h

# ---------------------------------------------------------------- CSV
def write_csv():
    p1x, p1y = P["pin1_x"], P["pin_y"]
    with open(OUT / "holes.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["name", "type", "x_mm", "y_mm", "x_from_pin1", "y_from_pin1", "hole", "pad (recommended)"])
        for n, t, x, y, d, pad in holes(): w.writerow([n, t, f"{x:.4f}", f"{y:.4f}", f"{x - p1x:.4f}", f"{y - p1y:.4f}", d, pad])
    for name, lay in (("leds_layout_B.csv", LAYOUT_B), ("leds_layout_A.csv", LAYOUT_A)):
        with open(OUT / name, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["designator (chain order)", "group", "x_mm", "y_mm", "x_from_pin1", "y_from_pin1", "rotation", "package"])
            for d, s, x, y in lay: w.writerow([d, {"L": "left column", "T": "top row", "R": "right column"}[s], f"{x:.4f}", f"{y:.4f}", f"{x - p1x:.4f}", f"{y - p1y:.4f}", 0, "WS2812B-2020 (2.0 x 2.0)"])
    with open(OUT / "buttons.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["designator", "x_mm", "y_mm", "x_from_pin1", "y_from_pin1", "note"])
        for d, x, y in BUTTONS: w.writerow([d, f"{x:.4f}", f"{y:.4f}", f"{x - p1x:.4f}", f"{y - p1y:.4f}", f"centred between side LEDs; {SIDE_CC - LED_SIZE:.2f} mm clear between LED bodies"])

# ---------------------------------------------------------------- DXF
def write_dxf():
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    for name, col in [("OUTLINE", 7), ("COURTYARD", 8), ("PTH", 1), ("NPTH", 5), ("VA", 4), ("AA", 30), ("LEDS_B", 3), ("LEDS_A", 6), ("BUTTONS", 2), ("TEXT", 7)]:
        doc.layers.add(name, color=col)
    rect = lambda x0, y0, x1, y1, layer: msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})
    rect(0, 0, P["lb_w"], P["lb_h"], "OUTLINE")
    rect(-KEEPOUT, -KEEPOUT, P["lb_w"] + KEEPOUT, P["lb_h"] + KEEPOUT, "COURTYARD")
    rect(P["va_x0"], P["va_y0"], P["va_x0"] + P["va_w"], P["va_y0"] + P["va_h"], "VA")
    rect(P["aa_x0"], P["aa_y0"], P["aa_x0"] + P["aa_w"], P["aa_y0"] + P["aa_h"], "AA")
    for n, t, x, y, *_ in holes():
        if t == "PTH": msp.add_circle((x, y), PIN_DRILL / 2, dxfattribs={"layer": "PTH"})
        elif t == "NPTH": msp.add_circle((x, y), PEG_DRILL / 2, dxfattribs={"layer": "NPTH"})
        else:                                            # rounded slot as a closed polyline with bulges
            hw, r = LED_SLOT[0] / 2 - LED_SLOT[1] / 2, LED_SLOT[1] / 2
            msp.add_lwpolyline([(x - hw, y - r, 0, 0, 0), (x + hw, y - r, 0, 0, 1), (x + hw, y + r, 0, 0, 0), (x - hw, y + r, 0, 0, 1)], format="xyseb", close=True, dxfattribs={"layer": "PTH"})
    for lay, layer in ((LAYOUT_B, "LEDS_B"), (LAYOUT_A, "LEDS_A")):
        for d, s, x, y in lay:
            rect(x - LED_SIZE / 2, y - LED_SIZE / 2, x + LED_SIZE / 2, y + LED_SIZE / 2, layer)
            msp.add_line((x - 0.4, y), (x + 0.4, y), dxfattribs={"layer": layer}); msp.add_line((x, y - 0.4), (x, y + 0.4), dxfattribs={"layer": layer})
            msp.add_text(d, height=0.8, dxfattribs={"layer": layer}).set_placement((x + 1.3, y + 1.3))
    for d, x, y in BUTTONS:
        msp.add_circle((x, y), 0.5, dxfattribs={"layer": "BUTTONS"}); msp.add_text(d, height=0.8, dxfattribs={"layer": "BUTTONS"}).set_placement((x + 1.3, y + 0.5))
    msp.add_text("WO240128A footprint, front / PCB top view, mm, origin = outline bottom-left", height=1.2, dxfattribs={"layer": "TEXT"}).set_placement((0, -6))
    msp.add_text("PIN 1", height=0.8, dxfattribs={"layer": "TEXT"}).set_placement((P["pin1_x"] - 1, P["pin_y"] + 1.2))
    doc.saveas(OUT / "WO240128A_pcb.dxf")

# ---------------------------------------------------------------- KiCad footprint (origin pin 1, Y down)
def write_kicad():
    p1x, p1y = P["pin1_x"], P["pin_y"]
    K = lambda x, y: (round(x - p1x, 4) + 0.0, round(p1y - y, 4) + 0.0)   # + 0.0 turns -0.0 into 0.0
    L = ['(footprint "WO240128A_COG_240x128" (version 20211014) (generator make_handoff) (layer "F.Cu")',
         '  (descr "Winstar WO240128A 240x128 COG LCD, UC1608; 23 pins P1.27, LED A/K tabs, 2 x dia 1.5 pegs; module sits on the top side, pins through")',
         '  (tags "LCD COG Winstar WO240128A UC1608") (attr through_hole)']
    (x0, y1), (x1, y0) = K(0, 0), K(P["lb_w"], P["lb_h"])
    L.append(f'  (fp_text reference "REF**" (at {(x0 + x1) / 2:.3f} {y0 - 1.5:.3f}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    L.append(f'  (fp_text value "WO240128A" (at {(x0 + x1) / 2:.3f} {(y0 + y1) / 2:.3f}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    L.append(f'  (fp_rect (start {x0} {y0}) (end {x1} {y1}) (layer "F.Fab") (width 0.1) (fill none))')
    L.append(f'  (fp_rect (start {x0 - 0.15} {y0 - 0.15}) (end {x1 + 0.15} {y1 + 0.15}) (layer "F.SilkS") (width 0.12) (fill none))')
    L.append(f'  (fp_rect (start {x0 - KEEPOUT} {y0 - KEEPOUT}) (end {x1 + KEEPOUT} {y1 + KEEPOUT}) (layer "F.CrtYd") (width 0.05) (fill none))')
    for nm, xx, yy, w, h in (("AA", P["aa_x0"], P["aa_y0"], P["aa_w"], P["aa_h"]), ("VA", P["va_x0"], P["va_y0"], P["va_w"], P["va_h"])):
        (a, b), (c, d) = K(xx, yy), K(xx + w, yy + h)
        L.append(f'  (fp_rect (start {a} {d}) (end {c} {b}) (layer "F.Fab") (width 0.1) (fill none))')
    L.append('  (fp_poly (pts (xy -0.6 2.4) (xy 0.6 2.4) (xy 0 1.7)) (layer "F.SilkS") (width 0.1) (fill solid))')   # pin-1 arrow, just outside the body edge
    for n, t, x, y, *_ in holes():
        kx, ky = K(x, y)
        if t == "PTH": L.append(f'  (pad "{n}" thru_hole {"rect" if n == "1" else "oval"} (at {kx} {ky}) (size {PIN_PAD[0]} {PIN_PAD[1]}) (drill {PIN_DRILL}) (layers "*.Cu" "*.Mask"))')
        elif t == "NPTH": L.append(f'  (pad "" np_thru_hole circle (at {kx} {ky}) (size {PEG_DRILL} {PEG_DRILL}) (drill {PEG_DRILL}) (layers "*.Cu" "*.Mask"))')
        else: L.append(f'  (pad "{n}" thru_hole oval (at {kx} {ky}) (size {LED_PAD[0]} {LED_PAD[1]}) (drill oval {LED_SLOT[0]} {LED_SLOT[1]}) (layers "*.Cu" "*.Mask"))')
    L.append(")")
    (OUT / "WO240128A_COG.kicad_mod").write_text("\n".join(L) + "\n")

# ---------------------------------------------------------------- PDF
INK, BLUE, RED, GREEN, GREY, ORANGE = (0.1, 0.1, 0.12), (0.12, 0.47, 0.76), (0.8, 0.15, 0.1), (0.1, 0.55, 0.25), (0.6, 0.6, 0.62), (0.88, 0.47, 0.12)
class Sheet:
    def __init__(self, c, ox, oy, s): self.c, self.ox, self.oy, self.s = c, ox, oy, s
    def X(self, x): return (self.ox + x * self.s) * mm
    def Y(self, y): return (self.oy + y * self.s) * mm
    def col(self, rgb, w=0.25, dash=None):
        self.c.setStrokeColorRGB(*rgb); self.c.setFillColorRGB(*rgb); self.c.setLineWidth(w); self.c.setDash(*(dash or []))
    def rect(self, x0, y0, w, h, rgb=INK, lw=0.35, fill=0, dash=None):
        self.col(rgb, lw, dash); self.c.rect(self.X(x0), self.Y(y0), w * self.s * mm, h * self.s * mm, stroke=1, fill=fill); self.c.setDash()
    def circle(self, x, y, d, rgb=RED, lw=0.3, fill=0): self.col(rgb, lw); self.c.circle(self.X(x), self.Y(y), d / 2 * self.s * mm, stroke=1, fill=fill)
    def slot(self, x, y, w, h, rgb=RED):
        self.col(rgb, 0.3); r = h / 2 * self.s * mm
        self.c.roundRect(self.X(x - w / 2), self.Y(y - h / 2), w * self.s * mm, h * self.s * mm, r, stroke=1, fill=0)
    def text(self, x, y, s, size=7, rgb=INK, anchor="l", rot=0):
        self.col(rgb); self.c.setFont("Helvetica", size); self.c.saveState(); self.c.translate(self.X(x), self.Y(y)); self.c.rotate(rot)
        {"l": self.c.drawString, "c": self.c.drawCentredString, "r": self.c.drawRightString}[anchor](0, 0, s); self.c.restoreState()
    def dim(self, a, b, off, label=None, rgb=BLUE, size=6.5):
        """CAD dimension between points a and b (model mm), dimension line `off` mm (model) out along the left normal of a->b."""
        (ax, ay), (bx, by) = a, b; L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux
        A = (ax + nx * off, ay + ny * off); B = (bx + nx * off, by + ny * off); g = 0.6 / self.s; e = 1.2 / self.s
        sgn = 1 if off >= 0 else -1
        self.col(rgb, 0.2)
        for (px, py), (qx, qy) in (((ax + nx * g * sgn, ay + ny * g * sgn), (A[0] + nx * e * sgn, A[1] + ny * e * sgn)), ((bx + nx * g * sgn, by + ny * g * sgn), (B[0] + nx * e * sgn, B[1] + ny * e * sgn))):
            self.c.line(self.X(px), self.Y(py), self.X(qx), self.Y(qy))
        self.c.line(self.X(A[0]), self.Y(A[1]), self.X(B[0]), self.Y(B[1]))
        ah, aw = 1.8 / self.s, 0.55 / self.s
        for (tx, ty), d in ((A, 1), (B, -1)):
            p = self.c.beginPath(); p.moveTo(self.X(tx), self.Y(ty))
            p.lineTo(self.X(tx + ux * ah * d + nx * aw), self.Y(ty + uy * ah * d + ny * aw)); p.lineTo(self.X(tx + ux * ah * d - nx * aw), self.Y(ty + uy * ah * d - ny * aw)); p.close()
            self.c.drawPath(p, stroke=0, fill=1)
        mx, my = (A[0] + B[0]) / 2 + nx * (1.0 / self.s) * sgn, (A[1] + B[1]) / 2 + ny * (1.0 / self.s) * sgn
        self.text(mx, my - (0.8 / self.s if sgn < 0 and abs(ux) > 0.5 else 0), label or f"{L:.2f}".rstrip("0").rstrip("."), size, rgb, "c", math.degrees(math.atan2(uy, ux)))

def frame(c, title, sub, scale_txt, page, pages):
    W, H = landscape(A4); c.setStrokeColorRGB(*INK); c.setLineWidth(0.5); c.rect(8 * mm, 8 * mm, W - 16 * mm, H - 16 * mm)
    c.rect(W - 128 * mm, 8 * mm, 120 * mm, 22 * mm)
    c.setFillColorRGB(*INK); c.setFont("Helvetica-Bold", 10); c.drawString(W - 125 * mm, 23 * mm, title)
    c.setFont("Helvetica", 7); c.drawString(W - 125 * mm, 18 * mm, sub)
    c.drawString(W - 125 * mm, 13 * mm, f"PerchWerks datalogger · WO240128A · mm · {scale_txt} · sheet {page}/{pages}")
    c.drawString(W - 125 * mm, 9.6 * mm, "Front / PCB top view. Origin: outline bottom-left. Generated by src/make_handoff.py")

def module_view(sh, holes_too=True, aa_va=True):
    sh.rect(0, 0, P["lb_w"], P["lb_h"], INK, 0.5)
    sh.rect(-KEEPOUT, -KEEPOUT, P["lb_w"] + 2 * KEEPOUT, P["lb_h"] + 2 * KEEPOUT, GREY, 0.2, dash=[2, 2])
    if aa_va:
        sh.rect(P["va_x0"], P["va_y0"], P["va_w"], P["va_h"], BLUE, 0.25, dash=[3, 1.5]); sh.rect(P["aa_x0"], P["aa_y0"], P["aa_w"], P["aa_h"], ORANGE, 0.25, dash=[1, 1])
    if holes_too:
        for n, t, x, y, *_ in holes():
            if t == "PTH": sh.circle(x, y, PIN_DRILL)
            elif t == "NPTH": sh.circle(x, y, PEG_DRILL, GREEN)
            else: sh.slot(x, y, *LED_SLOT)

def page_footprint(c):
    frame(c, "WO240128A — PCB footprint", "Hole pattern for the module's bent pins, LED tabs and locating pegs", "scale 1.5:1", 1, 5)
    sh = Sheet(c, 30, 64, 1.5); module_view(sh)
    sh.dim((0, P["lb_h"]), (P["lb_w"], P["lb_h"]), 4, f"{P['lb_w']} ±0.5")
    sh.dim((0, 0), (0, P["lb_h"]), 6, f"{P['lb_h']} ±0.5")
    sh.dim((0, 0), (P["pin1_x"], 0), -5, f"{P['pin1_x']} (pin 1)")
    p23 = P["pin1_x"] + 22 * P["pin_pitch"]
    sh.dim((P["pin1_x"], 0), (p23, 0), -5, f"22 × {P['pin_pitch']} = {22 * P['pin_pitch']:.2f}")
    sh.dim((0, 0), (P["led_a_x"], 0), -11, f"{P['led_a_x']} (A)")
    sh.dim((P["led_a_x"], 0), (P["led_k_x"], 0), -11, f"{P['led_k_x'] - P['led_a_x']:.1f} (A–K)")
    sh.dim((0, 0), (P["peg_x"], 0), -17, f"{P['peg_x']}")
    sh.dim((P["peg_x"], 0), (P["lb_w"] - P["peg_x"], 0), -17, f"{P['lb_w'] - 2 * P['peg_x']:.1f} (pegs)")
    sh.dim((P["lb_w"], 0), (P["lb_w"], P["pin_y"]), -4, f"{P['pin_y']} (pins)", size=5.5)
    sh.dim((P["lb_w"], 0), (P["lb_w"], P["led_pin_y"]), -13, f"{P['led_pin_y']} (A/K, pegs)", size=5.5)
    sh.text(P["pin1_x"] - 1.5, 4.2, "PIN 1", 6, RED, "l")
    sh.text(P["led_a_x"], 4.6, "A", 7, RED, "c"); sh.text(P["led_k_x"], 4.6, "K", 7, RED, "c")
    sh.text(P["lb_w"] / 2, P["aa_cy"], "AA 83.975 × 44.775 (orange) · VA 92.0 × 53.0 (blue) · module body = component keep-out", 7, GREY, "c")
    c.setFont("Helvetica-Bold", 7.5); c.setFillColorRGB(*INK); W = landscape(A4)[0]
    rows = [("Holes", " "), (f"23 × signal", f"PTH Ø{PIN_DRILL}, pad {PIN_PAD[0]}×{PIN_PAD[1]} oval (pin 1 rect)"),
            ("", "lead 0.40 × 0.25, P1.27, Y = 1.225"), ("2 × LED A / K", f"PTH slot {LED_SLOT[0]}×{LED_SLOT[1]}, pad {LED_PAD[0]}×{LED_PAD[1]}"),
            ("", "tab 1.8 × 0.5, Y = 2.25"), ("2 × pegs Ø1.5", f"NPTH Ø{PEG_DRILL}, Y = 2.25"), ("Courtyard", f"outline + {KEEPOUT}"), ("Body", "sits flat on the PCB: keep-out under it")]
    y = 190
    for a, b in rows:
        c.setFont("Helvetica-Bold" if b == " " else "Helvetica", 7); c.drawString(W - 92 * mm, y * mm, a); c.drawString(W - 72 * mm, y * mm, b); y -= 4.4
    c.setFont("Helvetica", 6.5)
    c.drawString(W - 92 * mm, (y - 2) * mm, "Exact coordinates: holes.csv · drill/pad sizes are")
    c.drawString(W - 92 * mm, (y - 5.5) * mm, "recommendations; outline, pin and peg positions are")
    c.drawString(W - 92 * mm, (y - 9) * mm, "from the Winstar drawing.")
    c.showPage()

def page_detail(c):
    frame(c, "Detail — pin row, LED tabs, pegs", "Bottom edge of the module, enlarged", "scale 4:1 (two halves)", 2, 5)
    for i, (x0, x1, oy) in enumerate(((0, 50, 145), (48.7, 98.7, 78))):
        sh = Sheet(c, 25 - x0 * 4, oy, 4)
        c.saveState(); pth = c.beginPath(); pth.rect(15 * mm, (oy - 22) * mm, 222 * mm, 70 * mm); c.clipPath(pth, stroke=0)
        sh.rect(0, 0, P["lb_w"], P["lb_h"], INK, 0.5)
        sh.rect(-KEEPOUT, -KEEPOUT, P["lb_w"] + 2 * KEEPOUT, P["lb_h"] + 2 * KEEPOUT, GREY, 0.2, dash=[2, 2])
        for n, t, x, y, *_ in holes():
            if not (x0 - 2 <= x <= x1 + 2): continue
            if t == "PTH":
                sh.col(GREY, 0.2); pw, ph = PIN_PAD; c.roundRect(sh.X(x - pw / 2), sh.Y(y - ph / 2), pw * 4 * mm, ph * 4 * mm, pw / 2 * 4 * mm, stroke=1, fill=0)
                sh.circle(x, y, PIN_DRILL); sh.text(x, y + 1.4, n, 5.5, RED, "c")
            elif t == "NPTH": sh.circle(x, y, PEG_DRILL, GREEN); sh.text(x, y + 1.4, "NPTH Ø1.6", 5.5, GREEN, "c")
            else:
                sh.col(GREY, 0.2); pw, ph = LED_PAD; c.roundRect(sh.X(x - pw / 2), sh.Y(y - ph / 2), pw * 4 * mm, ph * 4 * mm, ph / 2 * 4 * mm, stroke=1, fill=0)
                sh.slot(x, y, *LED_SLOT); sh.text(x, y + 1.4, n, 7, RED, "c")
        c.restoreState()
        if i == 0:
            sh.dim((0, 0), (P["peg_x"], 0), -2.5, f"{P['peg_x']}"); sh.dim((0, 0), (P["led_a_x"], 0), -4.5, f"{P['led_a_x']}")
            sh.dim((0, 0), (P["pin1_x"], 0), -6.5, f"{P['pin1_x']}")
            sh.dim((P["pin1_x"], P["pin_y"]), (P["pin1_x"] + P["pin_pitch"], P["pin_y"]), 2.2, f"{P['pin_pitch']}")
            sh.dim((x0 + 0.3, 0), (x0 + 0.3, P["led_pin_y"]), 1.5, f"{P['led_pin_y']}")
        else:
            sh.dim((P["led_k_x"], 0), (P["lb_w"], 0), -4.5, f"{P['lb_w'] - P['led_k_x']:.2f}")
            sh.dim((P["lb_w"] - P["peg_x"], 0), (P["lb_w"], 0), -2.5, f"{P['peg_x']}")
            sh.dim((P["pin1_x"] + 22 * P["pin_pitch"], 0), (P["lb_w"], 0), -6.5, f"{P['lb_w'] - P['pin1_x'] - 22 * P['pin_pitch']:.2f}")
    c.setFont("Helvetica", 7); c.setFillColorRGB(*INK)
    c.drawString(20 * mm, 40 * mm, f"Signal-pin row at Y = {P['pin_y']}; A/K tabs and pegs at Y = {P['led_pin_y']}.")
    c.drawString(20 * mm, 36 * mm, f"Grey = recommended pads. Signal: Ø{PIN_DRILL} drill, {PIN_PAD[0]}×{PIN_PAD[1]} oval (0.27 copper gap at P1.27). LED tabs: {LED_SLOT[0]}×{LED_SLOT[1]} slot, {LED_PAD[0]}×{LED_PAD[1]} pad. Pegs: Ø{PEG_DRILL} NPTH.")
    c.showPage()

def page_leds(c):
    frame(c, "LED + button placement — layout B (5 top + 3 + 3)", "11 × WS2812B-2020 on the PCB top side, D1–D11 in data-chain order", "scale 1.6:1", 3, 5)
    sh = Sheet(c, 58, 66, 1.6); module_view(sh, holes_too=False)
    for d, s, x, y in LAYOUT_B:
        sh.rect(x - LED_SIZE / 2, y - LED_SIZE / 2, LED_SIZE, LED_SIZE, GREEN, 0.35, fill=0); sh.text(x + 1.6, y + 1.4, d, 6, GREEN)
    for d, s, x, y in LAYOUT_A:                                       # the two extra top positions of layout A, ghosted
        if s == "T" and (abs(x - LED_SIZE / 2) < 0.01 or abs(x - (P["lb_w"] - LED_SIZE / 2)) < 0.01): sh.rect(x - LED_SIZE / 2, y - LED_SIZE / 2, LED_SIZE, LED_SIZE, GREY, 0.2, dash=[1, 1])
    for d, x, y in BUTTONS:
        sh.col(ORANGE, 0.3); c.line(sh.X(x - 1.5), sh.Y(y), sh.X(x + 1.5), sh.Y(y)); c.line(sh.X(x), sh.Y(y - 1.5), sh.X(x), sh.Y(y + 1.5)); sh.text(x + (2 if x > 0 else -2), y - 0.6, d, 6, ORANGE, "l" if x > 0 else "r")
    T = [q for q in LAYOUT_B if q[1] == "T"]; Lc = sorted([q for q in LAYOUT_B if q[1] == "L"], key=lambda q: q[3])
    ytop = P["lb_h"] + LED_GAP
    sh.dim((T[2][2], ytop), (T[3][2], ytop), 4, f"{pitch:.3f}")
    sh.dim((0, P["lb_h"]), (T[0][2], P["lb_h"]), 9, f"{T[0][2]:.3f}")
    sh.dim((P["lb_w"], P["lb_h"]), (P["lb_w"], ytop), -3, f"{LED_GAP}*")
    sh.dim((Lc[0][2], Lc[0][3]), (Lc[1][2], Lc[1][3]), 4, f"{SIDE_CC:.2f}"); sh.dim((Lc[1][2], Lc[1][3]), (Lc[2][2], Lc[2][3]), 4, f"{SIDE_CC:.2f}")
    sh.dim((Lc[0][2], 0), (0, 0), 5, f"{LED_SIDE}*")
    sh.dim((P["lb_w"] + LED_SIDE, 0), (P["lb_w"] + LED_SIDE, Lc[0][3]), -6, f"{Lc[0][3]:.3f} (AA bottom)")
    sh.dim((P["lb_w"] + LED_SIDE, 0), (P["lb_w"] + LED_SIDE, Lc[1][3]), -11, f"{Lc[1][3]:.2f} (AA middle)")
    sh.dim((P["lb_w"] + LED_SIDE, 0), (P["lb_w"] + LED_SIDE, Lc[2][3]), -16, f"{Lc[2][3]:.3f} (AA top)")
    c.setFont("Helvetica", 7); c.setFillColorRGB(*INK)
    notes = [f"Top row: 5 of 7 positions on a {pitch:.4f} pitch; the 7 would sit flush with the outline (grey = the 2 extra of layout A).",
             f"Side columns {LED_SIDE} mm out from the outline, level with the AA top / middle / bottom; {SIDE_CC:.2f} c–c, {SIDE_CC - LED_SIZE:.2f} clear for the buttons.",
             "SW1–SW4: suggested button centres, midway between side LEDs. Chain: up the left column, along the top, down the right.",
             "* placeholders until the enclosure is drawn: top-row gap above the outline (3.0) and side-column offset (5.0).",
             "The LEDs sit on the PCB, 5.7 mm below the glass front face: plan light pipes or a stepped bezel. Full list: leds_layout_B.csv / _A.csv."]
    for i, s in enumerate(notes): c.drawString(18 * mm, (54 - i * 3.6) * mm, s)
    c.showPage()

def page_check(c):
    frame(c, "1:1 check print", "Print at 100 % (no fit-to-page) and check the 50 mm bar, then lay the module or PCB on it", "scale 1:1", 4, 5)
    sh = Sheet(c, 70, 60, 1); module_view(sh)
    for d, s, x, y in LAYOUT_B: sh.rect(x - LED_SIZE / 2, y - LED_SIZE / 2, LED_SIZE, LED_SIZE, GREEN, 0.3)
    for d, x, y in BUTTONS: sh.circle(x, y, 1.0, ORANGE)
    sh.col(INK, 0.6); c.line(sh.X(0), sh.Y(-20), sh.X(50), sh.Y(-20))
    for x in range(0, 51, 10): c.line(sh.X(x), sh.Y(-21), sh.X(x), sh.Y(-19))
    sh.text(25, -24, "50 mm", 8, INK, "c")
    c.showPage()

def page_notes(c):
    frame(c, "Notes for layout", "What the drawing fixes, what is ours to choose", "—", 5, 5)
    W, H = landscape(A4); y = H - 20 * mm; c.setFillColorRGB(*INK)
    lines = [("b", "Module: Winstar WO240128A, 240 × 128 COG (UC1608), outline 98.7 × 67.7 ±0.5, 9.5 overall (to the A/K tips)."),
             ("", "Mounting: the module lies flat on the PCB top side, frame rear face on the board; pins, A/K tabs and pegs go through."),
             ("", "Glass front face is 5.7 above the PCB (2.9 glass + 2.8 backlight). The whole 98.7 × 67.7 body is a component keep-out on top."),
             ("", f"Lead lengths below the frame rear face: signal pins {P['lcd_t'] + P['pin_len'] - (P['lcd_t'] + P['lb_t']):.1f}, A/K tabs {P['led_pin_len']}, pegs {P['peg_len']} — trim or allow for them under a 1.6 PCB."),
             ("", "Pin 1 is the leftmost signal pin seen from the front (X 35.38). Check the pin-out table on the datasheet revision you buy."),
             ("b", "From the drawing: outline, pin positions / pitch, A/K and peg positions. Estimated: A/K tab thickness, chip size."),
             ("b", "Recommended (ours): drill and pad sizes — " + f"signal Ø{PIN_DRILL} / {PIN_PAD[0]}×{PIN_PAD[1]} oval, A/K slot {LED_SLOT[0]}×{LED_SLOT[1]} / {LED_PAD[0]}×{LED_PAD[1]}, pegs NPTH Ø{PEG_DRILL}."),
             ("", "If your fab's minimum annular ring or slot rules differ, keep the hole centres and adjust sizes."),
             ("b", "LEDs: 11 × WS2812B-2020 (2.0 × 2.0 × ~0.84), chain D1→D11 = up the left column, along the top, down the right."),
             ("", "Roles in firmware: top row = pace, side columns = status (overheat, rev limit, grip), all = purple sector / best lap."),
             ("", "Budget ~15 mA per LED at full white (5 mA/colour 2020 types; some are 12 mA/colour — check the part), ~0.5–1 mA idle each."),
             ("", "Consider a load switch on the LED 5 V rail so firmware can cut the idle current, and a 3.3 V→5 V level shifter on DIN."),
             ("b", "Files: holes.csv (from pin 1 and from the corner), leds_layout_B/A.csv, buttons.csv, WO240128A_pcb.dxf (layered),"),
             ("", "WO240128A_COG.kicad_mod (origin pin 1), plus ../scad (OpenSCAD source: footprint / bezel modes) and ../exports (STL, DXF)."),
             ("", "Regenerate after any change: python3 src/make_handoff.py (reads the .scad).")]
    for kind, s in lines:
        c.setFont("Helvetica-Bold" if kind == "b" else "Helvetica", 8.5); c.drawString(20 * mm, y, s); y -= 6.2 * mm
    c.showPage()

def write_pdf():
    c = canvas.Canvas(str(OUT / "WO240128A_pcb_handoff.pdf"), pagesize=landscape(A4))
    c.setTitle("WO240128A PCB handoff"); c.setAuthor("PerchWerks")
    page_footprint(c); page_detail(c); page_leds(c); page_check(c); page_notes(c); c.save()

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    write_csv(); write_dxf(); write_kicad(); write_pdf()
    for f in sorted(OUT.iterdir()): print(f"wrote {f.relative_to(ROOT)}  ({f.stat().st_size / 1024:.0f} KB)")
