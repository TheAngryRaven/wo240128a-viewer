// =====================================================================
//  Winstar WO240128A-class 240x128 COG graphic LCD (UC1608) -- OpenSCAD model
//  Transcribed from the Winstar outline drawing (98.7 x 67.7 mm LB outline,
//  96.0 x 65.0 mm glass, VA 92.0 x 53.0, AA 83.975 x 44.775, 23 pins @ 1.27,
//  LED pins A/K, 2 x dia 1.5 locating pegs, 9.5 mm max overall thickness).
//
//  Units: mm.
//  Coordinate frame (matches the drawing's FRONT view):
//     +X = right, +Y = up, +Z = toward the viewer (out of the glass).
//     Z = 0 is the glass FRONT face. Everything else lies at Z < 0.
//     The pins and pegs are bent 90 deg and point toward -Z (into the PCB),
//     so the module lies flat on a PCB with the frame's rear face on it.
//
//  Origin choices (see `origin` below):
//     lb_center  = centre of the 98.7 x 67.7 outline (default)
//     aa_center  = centre of the 240x128 active area (handy for bezel cut-outs)
//     lb_corner  = bottom-left corner of the outline
//     pin1       = pin-1 leg centreline (handy for PCB alignment)
//
//  Modes:
//     mode = "3d"        full model
//     mode = "footprint" 2D outline + hole pattern in the PCB plane (export DXF)
//     mode = "bezel"     2D cut-out helper (VA / AA / glass outlines)
//
//  Dimensions marked (est.) were scaled off the drawing, not dimensioned on it.
//  Pin-tab height, A/K pin thickness, chip size and the pull-tape length are
//  cosmetic; everything that affects a PCB or bezel is from the drawing.
// =====================================================================

/* [Output] */
mode   = "3d";        // ["3d", "footprint", "bezel"]
origin = "lb_center"; // ["lb_center", "aa_center", "lb_corner", "pin1"]

/* [Show / hide] */
show_frame     = true;
show_glass     = true;
show_pins      = true;
show_led_pins  = true;
show_pegs      = true;
show_chip      = true;
show_pull_tape = true;
show_va_aa     = true;   // tint the viewing / active areas on the glass
show_dots      = false;  // draw the 240x128 dot matrix (30,720 cubes: preview only, slow)
dot_step       = 4;      // when show_dots: draw every Nth dot (1 = all)
explode        = 0;      // pull the glass / frame / pins apart along Z (mm)

/* [Resolution] */
$fn = 32;

/* [LB outline: backlight + frame] */
lb_w       = 98.7;   // +/-0.5
lb_h       = 67.7;   // +/-0.5
lb_t       = 2.8;    // backlight thickness +/-0.3 (behind the glass)
frame_wall = 1.35;   // side/top wall = (lb_w - lcd_w)/2 = (lb_h - lcd_h)/2
foot_w     = 6.4;    // end caps at the two bottom corners (est.)
foot_h     = 1.35;   // they reach 1.35 below the glass bottom edge

/* [LCD glass] */
lcd_w   = 96.0;      // +/-0.2
lcd_h   = 65.0;      // +/-0.2
lcd_t   = 2.9;       // 2.9 MAX (2 x 1.1 glass + polarizers)
ledge_h = 8.0;       // COG ledge: the front plate stops 8.0 above the bottom edge

/* [Viewing area / active area (drawing references them to the LB outline)] */
va_w = 92.0;  va_h = 53.0;
va_x0 = 3.35;         // LB left edge -> VA left edge
va_ytop = 3.35;       // LB top edge  -> VA top edge
aa_w = 83.975; aa_h = 44.775;
aa_x0 = 7.3625;       // (lb_w - aa_w)/2  (drawing: 7.363)
aa_ytop = 6.1125;     // LB top edge -> AA top edge
cols = 240; rows = 128;
dot_pitch = 0.35; dot_size = 0.325;

/* [Signal pins (23 x, bent 90 deg toward the rear)] */
n_pins    = 23;
pin_pitch = 1.27;     // P1.27 x 22 = 27.94
pin1_x    = 35.38;    // LB left edge -> pin 1 centre
pin_w     = 0.40;
pin_t     = 0.25;     // +/-0.05
pin_tab_h = 2.6;      // vertical tab soldered on the ledge (est.)
pin_len   = 8.0;      // +/-0.5, measured from the LCD rear face to the tip
pin_y     = 1.225;    // leg centreline above LB bottom edge (drawing: 66.475 from top)

/* [LED backlight pins A / K] */
led_pin_w   = 1.8;
led_pin_t   = 0.5;    // (est.)
led_a_x     = 19.35;  // LB left edge -> A centre
led_k_x     = 79.35;  // = 19.35 + 60.0
led_pin_len = 3.8;    // beyond the frame rear face  (5.7 + 3.8 = 9.5 overall)
led_pin_y   = 2.25;   // centreline above LB bottom edge (drawing: 65.45 from top)

/* [Locating pegs 2 x dia 1.5] */
peg_d   = 1.5;
peg_len = 2.0;        // beyond the frame rear face
peg_x   = 1.83;       // LB left edge -> peg centre  (95.0 between centres)
peg_y   = 2.25;

/* [Cosmetic details] */
chip_w = 10.9; chip_h = 1.7; chip_t = 0.3; chip_y = 6.65;   // UC1608 on the ledge (est.)
tape_len = 13.0; tape_h = 8.0; tape_t = 0.1; tape_overhang = 3.65; // pull tape, top-right
notch_len = 10.0; notch_top = 23.5; notch_depth = 1.85;      // side-wall notch: 10.0 MAX, 23.5 MIN from top

/* [PCB footprint holes (mode = "footprint")] */
pin_hole_d  = 0.9;
peg_hole_d  = 1.6;
led_hole    = [2.3, 1.0];   // slot for the 1.8 x 0.5 LED pins
keepout     = 0.5;          // courtyard margin around the LB outline

// ---------------------------------------------------------------------
//  Derived values
// ---------------------------------------------------------------------
total_t   = lcd_t + lb_t;                 // 5.7 : glass front -> frame rear
lcd_x0    = (lb_w - lcd_w) / 2;           // 1.35
lcd_y0    = (lb_h - lcd_h) / 2;           // 1.35
plate_t   = lcd_t / 2;                    // each glass plate incl. polarizer
ledge_z   = -plate_t;                     // front face of the rear plate (pads + chip live here)
va_y0     = lb_h - va_ytop - va_h;        // 11.35
aa_y0     = lb_h - aa_ytop - aa_h;        // 16.8125
aa_cx     = aa_x0 + aa_w / 2;             // 49.35
aa_cy     = aa_y0 + aa_h / 2;             // 39.2
pin_tip_z = -(lcd_t + pin_len);           // -10.9
led_tip_z = -(total_t + led_pin_len);     // -9.5
peg_tip_z = -(total_t + peg_len);         // -7.7
eps = 0.01;

function pin_x(n) = pin1_x + (n - 1) * pin_pitch;    // n = 1..23, LB-corner frame
function pin_pos(n) = [pin_x(n), pin_y];              // PCB-plane position of pin n

function origin_shift() =
    origin == "aa_center" ? [-aa_cx, -aa_cy, 0] :
    origin == "lb_corner" ? [0, 0, 0] :
    origin == "pin1"      ? [-pin1_x, -pin_y, 0] :
                            [-lb_w / 2, -lb_h / 2, 0];

// ---------------------------------------------------------------------
//  Colours
// ---------------------------------------------------------------------
c_frame = [0.93, 0.93, 0.90];
c_glass = [0.62, 0.78, 0.70, 0.45];
c_va    = [0.84, 0.88, 0.80];
c_aa    = [0.77, 0.83, 0.74];
c_dot   = [0.25, 0.30, 0.25];
c_metal = [0.78, 0.78, 0.80];
c_chip  = [0.12, 0.12, 0.12];
c_tape  = [0.95, 0.55, 0.15, 0.85];

// ---------------------------------------------------------------------
//  Parts (all built in the LB-corner frame: X from the left edge, Y from the
//  bottom edge, Z from the glass front face)
// ---------------------------------------------------------------------

module side_notch(x_wall) {
    // rounded slot through the side wall, open toward the front face
    yc = lb_h - notch_top - notch_len / 2;
    r  = frame_wall / 2;
    hull()
        for (y = [yc - notch_len / 2 + r, yc + notch_len / 2 - r])
            translate([x_wall + frame_wall / 2, y, -notch_depth])
                cylinder(r = r, h = notch_depth + 1);
}

module frame() {
    color(c_frame) {
        difference() {
            // cradle: full outline above the feet line, full thickness
            translate([0, lcd_y0, -total_t]) cube([lb_w, lb_h - lcd_y0, total_t]);
            // pocket the glass sits in (leaves the backlight behind it)
            translate([lcd_x0, lcd_y0 - 1, -lcd_t]) cube([lcd_w, lcd_h + 1, lcd_t + 1]);
            // glue/tape notches in both side walls
            side_notch(0);
            side_notch(lb_w - frame_wall);
        }
        // end caps / feet at the two bottom corners
        for (x = [0, lb_w - foot_w])
            translate([x, 0, -total_t]) cube([foot_w, foot_h + eps, total_t]);
    }
}

module glass() {
    // rear plate: full height, its bottom 8 mm is the COG ledge
    color(c_glass) translate([lcd_x0, lcd_y0, -lcd_t]) cube([lcd_w, lcd_h, plate_t]);
    // front plate: shorter by the ledge
    color(c_glass) translate([lcd_x0, lcd_y0 + ledge_h, -plate_t]) cube([lcd_w, lcd_h - ledge_h, plate_t]);
    if (show_va_aa) {
        color(c_va) translate([va_x0, va_y0, 0])       cube([va_w, va_h, eps]);
        color(c_aa) translate([aa_x0, aa_y0, eps])     cube([aa_w, aa_h, eps]);
    }
    if (show_dots) dots();
}

// One dot at column c (0..239, left->right) and row r (0..127, top->bottom)
module pixel(c, r, h = 0.03) {
    translate([aa_x0 + c * dot_pitch, lb_h - aa_ytop - r * dot_pitch - dot_size, 2 * eps])
        cube([dot_size, dot_size, h]);
}

module dots() {
    color(c_dot)
        for (c = [0 : dot_step : cols - 1], r = [0 : dot_step : rows - 1])
            pixel(c, r);
}

module signal_pin(n) {
    x = pin_x(n);
    color(c_metal) {
        // vertical tab on the ledge (rear plate's front face)
        translate([x - pin_w / 2, lcd_y0, ledge_z]) cube([pin_w, pin_tab_h, pin_t]);
        // leg wrapped under the glass bottom edge, running to the rear
        translate([x - pin_w / 2, pin_y - pin_t / 2, pin_tip_z])
            cube([pin_w, pin_t, -pin_tip_z + ledge_z + pin_t]);
    }
}

module led_pin(x) {
    color(c_metal)
        translate([x - led_pin_w / 2, led_pin_y - led_pin_t / 2, led_tip_z])
            cube([led_pin_w, led_pin_t, led_pin_len + 1]);   // +1 buried in the frame
}

module peg(x) {
    color(c_frame)
        translate([x, peg_y, peg_tip_z])
            cylinder(d1 = peg_d - 0.3, d2 = peg_d, h = 0.3);   // chamfered tip
    color(c_frame)
        translate([x, peg_y, peg_tip_z + 0.3])
            cylinder(d = peg_d, h = peg_len - 0.3 + eps);
}

module chip() {
    color(c_chip)
        translate([lb_w / 2 - chip_w / 2, chip_y - chip_h / 2, ledge_z])
            cube([chip_w, chip_h, chip_t]);
}

module pull_tape() {
    color(c_tape)
        translate([lb_w + tape_overhang - tape_len, lb_h - lcd_y0 - tape_h, 2 * eps])
            cube([tape_len, tape_h, tape_t]);
}

// ---------------------------------------------------------------------
//  Assembly
// ---------------------------------------------------------------------
module wo240128a() {
    if (show_frame) translate([0, 0, -explode]) frame();
    if (show_glass) glass();
    if (show_chip)  chip();
    if (show_pull_tape) pull_tape();
    translate([0, 0, -2 * explode]) {
        if (show_pins)     for (n = [1 : n_pins]) signal_pin(n);
        if (show_led_pins) { led_pin(led_a_x); led_pin(led_k_x); }
        if (show_pegs)     { peg(peg_x); peg(lb_w - peg_x); }
    }
}

// 2D: what the PCB sees (module lying flat, glass up). Export with File > Export > DXF.
module footprint_2d(stroke = 0.1) {
    // courtyard + body outline
    difference() { offset(delta = keepout) square([lb_w, lb_h]); offset(delta = keepout - stroke) square([lb_w, lb_h]); }
    difference() { square([lb_w, lb_h]); offset(delta = -stroke) square([lb_w, lb_h]); }
    // signal pins
    for (n = [1 : n_pins]) translate(pin_pos(n)) circle(d = pin_hole_d);
    // LED pins: rounded slots
    for (x = [led_a_x, led_k_x])
        translate([x, led_pin_y]) hull() for (s = [-1, 1])
            translate([s * (led_hole[0] - led_hole[1]) / 2, 0]) circle(d = led_hole[1]);
    // locating pegs
    for (x = [peg_x, lb_w - peg_x]) translate([x, peg_y]) circle(d = peg_hole_d);
}

// 2D: bezel / window helper (front view). AA = live pixels, VA = clear window.
module bezel_2d(stroke = 0.1) {
    difference() { square([lb_w, lb_h]); offset(delta = -stroke) square([lb_w, lb_h]); }
    translate([lcd_x0, lcd_y0]) difference() { square([lcd_w, lcd_h]); offset(delta = -stroke) square([lcd_w, lcd_h]); }
    translate([va_x0, va_y0])   difference() { square([va_w, va_h]);   offset(delta = -stroke) square([va_w, va_h]); }
    translate([aa_x0, aa_y0])   difference() { square([aa_w, aa_h]);   offset(delta = -stroke) square([aa_w, aa_h]); }
}

translate(origin_shift()) {
    if (mode == "3d")             wo240128a();
    else if (mode == "footprint") footprint_2d();
    else if (mode == "bezel")     bezel_2d();
}

// Handy numbers (relative to the LB bottom-left corner; add origin_shift() for your origin)
echo(str("Overall: ", lb_w, " x ", lb_h, " x ", -led_tip_z, " mm (frame rear face at Z=", -total_t, ")"));
echo(str("AA centre: X=", aa_cx, " Y=", aa_cy, "   VA: ", va_w, "x", va_h, " at X=", va_x0, " Y=", va_y0));
echo(str("Pin 1 leg: X=", pin1_x, " Y=", pin_y, "   pin 23: X=", pin_x(n_pins), "   pitch ", pin_pitch));
echo(str("A: X=", led_a_x, "  K: X=", led_k_x, "  Y=", led_pin_y, "   pegs: X=", peg_x, " & ", lb_w - peg_x, " Y=", peg_y));
echo(str("Origin shift applied (", origin, "): ", origin_shift()));
