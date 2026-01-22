import pygame
import math
import os
import secrets

from simulation.rng import RNGManager
from simulation.sweep import run_sweep

from config import *
from core.vector import Vector
from components.mirror import Mirror
from components.lensed_mirror import LensedMirror
from components.media_interface import MediaInterface
from components.lens import Lens
from components.detector import Detector
from components.media_polygon import MediaPolygon
from sources.beam import Beam
from sources.fiber import FiberSource
from simulation.scene import Scene
from simulation.tracer import trace_rays, trace_hits, trace_reference_events
from ui.grid import draw_grid
from ui.interaction import InteractionState
from ui.button import Button
from ui.collapsible_group import CollapsibleGroup
from ui.numeric_field import NumericField
from ui.overlay import draw_overlay_lines
from ui.snap import snap_point


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", FONT_SIZE)
font_small = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", FONT_SMALL_SIZE)


# --- Scene / state ---
scene = Scene()
scene.medium.alpha_per_um = ALPHA_PER_UM_DEFAULT
scene.medium.n = BACKGROUND_N_DEFAULT

interaction = InteractionState()
interaction.um_per_px = UM_PER_PX_DEFAULT
interaction.ref_d1_um = REF_D1_UM_DEFAULT
interaction.snap_enabled = SNAP_ENABLED_DEFAULT

# Experiment controls
sim_seed = SEED_DEFAULT
sim_sample_offset = 0
draw_rays_enabled = DRAW_RAYS_DEFAULT
max_rays = MAX_RAYS_DEFAULT
fiber_num_rays = FIBER_NUM_RAYS

rng_manager = RNGManager(sim_seed)

# Sweep controls
sweep_start = SWEEP_START_DEFAULT
sweep_stop = SWEEP_STOP_DEFAULT
sweep_step = SWEEP_STEP_DEFAULT
sweep_rays_cap = SWEEP_RAYS_PER_STEP_DEFAULT
sweep_base_seed = SEED_DEFAULT
sweep_last_msg = ""
template_last_msg = ""


# --- editor callbacks ---

def cb_add_fiber():
    interaction.add_mode = "fiber"


def cb_add_mirror():
    interaction.add_mode = "mirror"


def cb_add_lensed_mirror():
    interaction.add_mode = "lensed_mirror"


def cb_add_lens():
    interaction.add_mode = "lens"


def cb_add_detector():
    interaction.add_mode = "detector"


def cb_add_beam():
    interaction.add_mode = "beam"


def cb_add_media():
    interaction.add_mode = "media"


def cb_add_media_poly():
    interaction.add_mode = "media_poly"
    interaction.poly_points = []


def cb_load_reference_layout():
    """Populate the scene with a reference layout approximating the project diagram.

    This version is parameter-driven (angles + region extents) so it can be tuned
    and is more repeatable than the initial placeholder.
    """
    global template_last_msg, sweep_last_msg

    # Clear scene
    scene.objects = []
    interaction.selected = None
    interaction.add_mode = None
    interaction.poly_points = []
    interaction.current_pos = None
    interaction.start_pos = None
    sweep_last_msg = ""

    # Background (air)
    scene.medium.n = 1.0
    scene.medium.alpha_per_um = 0.0
    scene.medium.name = "air"

    # --- Parameters (edit later via Properties if needed) ---
    cfg = {
        # Refractive indices (from diagram ordering)
        "n_fiber": 1.4527,
        "n_adh": 1.4898,
        "n_ferr": 1.5218,

        # Angles (deg)
        "cleave_deg": 8.0,          # fiber facet tilt (from perpendicular)
        "wall_tilt_deg": 9.0,       # groove end wall tilt (from vertical)
        "lensed_mirror_deg": 43.4,  # lensed mirror chord angle (from +x)

        # Geometry (px)
        "fiber_len_px": 420.0,
        "fiber_h_px": 44.0,
        "adh_len_px": 220.0,
        "ferr_len_px": 520.0,
    }

    # Anchor within the canvas (top-left-ish, like the diagram)
    x0 = SIDEBAR_W + 90
    y0 = UI_BAR_H + 90

    fiber_len = cfg["fiber_len_px"]
    fiber_h = cfg["fiber_h_px"]
    x_fiber_l = x0
    x_fiber_r = x0 + fiber_len

    # --- Fiber region with a slanted facet (~8° from perpendicular) ---
    dx = math.tan(math.radians(cfg["cleave_deg"])) * fiber_h
    fiber_pts = [
        Vector(x_fiber_l, y0),
        Vector(x_fiber_r + dx * 0.5, y0),
        Vector(x_fiber_r - dx * 0.5, y0 + fiber_h),
        Vector(x_fiber_l, y0 + fiber_h),
    ]
    scene.add(MediaPolygon(fiber_pts, n=cfg["n_fiber"], alpha_per_um=0.0, name="fiber"))

    # --- Adhesive region (surrounding the fiber end) ---
    x_adh_l = x_fiber_r - 40
    x_adh_r = x_fiber_r + cfg["adh_len_px"]
    adh_pts = [
        Vector(x_adh_l, y0 - 40),
        Vector(x_adh_r, y0 - 40),
        Vector(x_adh_r, y0 + fiber_h + 220),
        Vector(x_adh_l, y0 + fiber_h + 220),
    ]
    scene.add(MediaPolygon(adh_pts, n=cfg["n_adh"], alpha_per_um=0.0, name="adhesive"))

    # --- Ferrule region (to the right, with a slight top slope like in the figure) ---
    x_ferr_l = x_adh_r - 10
    x_ferr_r = x_ferr_l + cfg["ferr_len_px"]
    ferr_top = y0 - 60
    ferr_bottom = y0 + fiber_h + 260
    ferr_pts = [
        Vector(x_ferr_l, ferr_top),
        Vector(x_ferr_r, ferr_top + 40),
        Vector(x_ferr_r, ferr_bottom),
        Vector(x_ferr_l, ferr_bottom),
    ]
    scene.add(MediaPolygon(ferr_pts, n=cfg["n_ferr"], alpha_per_um=0.0, name="ferrule"))

    # --- Beam source inside the fiber (vertical segment emitting to the right) ---
    bx = x_fiber_l + 80
    by = y0 + fiber_h * 0.5
    scene.add(
        Beam(
            Vector(bx, by + 18),  # p1 lower
            Vector(bx, by - 18),  # p2 upper -> chord points up, normal points +x
            spread_deg=6.0,
            pos_spacing_px=10.0,
            angle_samples=7,
            total_power=1.0,
        )
    )

    # --- Groove end wall (~9° from vertical) as a mirror segment ---
    wall_center = Vector(x_fiber_r + 45, y0 + fiber_h + 35)
    wall_L = 150.0
    wall_a = math.radians(90.0 + cfg["wall_tilt_deg"])  # near-vertical, tilted
    wx = math.cos(wall_a) * (wall_L * 0.5)
    wy = math.sin(wall_a) * (wall_L * 0.5)
    scene.add(Mirror(Vector(wall_center.x - wx, wall_center.y - wy), Vector(wall_center.x + wx, wall_center.y + wy)))

    # --- Tilted lensed mirror (~43.4°) ---
    lm_center = Vector(x_ferr_l + 320, y0 + 50)
    lm_L = 240.0
    lm_a = math.radians(cfg["lensed_mirror_deg"])
    mx1 = math.cos(lm_a) * (lm_L * 0.5)
    my1 = math.sin(lm_a) * (lm_L * 0.5)
    scene.add(LensedMirror(Vector(lm_center.x - mx1, lm_center.y - my1), Vector(lm_center.x + mx1, lm_center.y + my1), bulge=140.0))

    # --- Detector under the mirror (horizontal) ---
    det_y = ferr_bottom - 30
    scene.add(Detector(Vector(lm_center.x - 160, det_y), Vector(lm_center.x + 220, det_y)))

    template_last_msg = "Reference layout v2 loaded (fiber→adhesive→ferrule; wall≈9°; lensed mirror=43.4°)."


def cb_clear_media_interfaces():
    scene.clear_by_type(MediaInterface)


def cb_clear_media_polygons():
    scene.clear_by_type(MediaPolygon)


def cb_clear_fiber():
    scene.clear_by_type(FiberSource)
    scene.clear_by_type(MediaInterface)


def cb_clear_mirrors():
    scene.clear_by_type(Mirror)


def cb_clear_lensed_mirrors():
    scene.clear_by_type(LensedMirror)


def cb_clear_lenses():
    scene.clear_by_type(Lens)


def cb_clear_detectors():
    scene.clear_by_type(Detector)


def cb_clear_beams():
    scene.clear_by_type(Beam)


# --- Experiment controls callbacks ---

def _effective_seed() -> int:
    return int(sim_seed) + int(sim_sample_offset)


def cb_new_sample():
    global sim_sample_offset
    sim_sample_offset += 1


def cb_reseed_random():
    global sim_seed, sim_sample_offset
    sim_seed = int(secrets.randbelow(10**9))
    sim_sample_offset = 0
    rng_manager.set_seed(_effective_seed())


def set_seed_from_field(v):
    global sim_seed, sim_sample_offset
    sim_seed = int(round(v))
    sim_sample_offset = 0
    rng_manager.set_seed(_effective_seed())


def set_draw_from_field(v):
    global draw_rays_enabled
    draw_rays_enabled = bool(int(round(v)))


def set_max_rays_from_field(v):
    global max_rays
    max_rays = int(max(0, round(v)))


def set_fiber_rays_from_field(v):
    global fiber_num_rays
    fiber_num_rays = int(max(0, round(v)))


# --- Sweep callbacks / setters ---

def set_sweep_start_from_field(v):
    global sweep_start
    sweep_start = float(v)


def set_sweep_stop_from_field(v):
    global sweep_stop
    sweep_stop = float(v)


def set_sweep_step_from_field(v):
    global sweep_step
    sweep_step = float(v)


def set_sweep_rays_from_field(v):
    global sweep_rays_cap
    sweep_rays_cap = int(max(1, round(v)))


def set_sweep_seed_from_field(v):
    global sweep_base_seed
    sweep_base_seed = int(round(v))


def _sweep_target_from_selection():
    """Return (target_name, get_param, set_param) or None."""
    sel = interaction.selected
    um = float(interaction.um_per_px) if interaction.um_per_px else 1.0

    if isinstance(sel, Lens):
        return (
            "Lens_f_um",
            lambda: sel.f * um,
            lambda vv: setattr(sel, "f", float(vv) / um),
        )
    if isinstance(sel, LensedMirror):
        return (
            "LensedMirror_bulge_um",
            lambda: sel.bulge * um,
            lambda vv: setattr(sel, "bulge", float(vv) / um),
        )
    if isinstance(sel, MediaPolygon):
        return (
            "MediaPolygon_n",
            lambda: float(sel.medium.n),
            lambda vv: setattr(sel.medium, "n", float(vv)),
        )
    if isinstance(sel, Beam):
        return (
            "Beam_spread_deg",
            lambda: float(sel.spread_deg),
            lambda vv: setattr(sel, "spread_deg", float(vv)),
        )
    return None


def cb_run_sweep():
    global sweep_last_msg
    target = _sweep_target_from_selection()
    if target is None:
        sweep_last_msg = "Sweep: select Lens (f), LensedMirror (bulge), MediaPolygon (n) or Beam (spread)."
        return

    target_name, get_param, set_param = target

    # Use the app folder for exports (portable on Windows).
    exports_dir = os.path.join(os.path.dirname(__file__), "exports")

    # For sweeps, use a deterministic per-step seed (base_seed + i).
    try:
        out_path, _rows = run_sweep(
            scene=scene,
            emit_rays=lambda rng: _emit_rays(rng, fiber_rays_override=sweep_rays_cap, cap=sweep_rays_cap),
            rng_manager=rng_manager,
            um_per_px=float(interaction.um_per_px) if interaction.um_per_px else 1.0,
            target_name=target_name,
            get_param=get_param,
            set_param=set_param,
            start=float(sweep_start),
            stop=float(sweep_stop),
            step=float(sweep_step),
            rays_per_step_cap=int(sweep_rays_cap),
            base_seed=int(sweep_base_seed),
            exports_dir=exports_dir,
        )
        sweep_last_msg = f"Sweep saved: {out_path}"
    except Exception as ex:
        sweep_last_msg = f"Sweep error: {type(ex).__name__}: {ex}"


# --- Sidebar groups (expandable) ---
properties_group = CollapsibleGroup("Properties", [], expanded=True)

groups = [
    CollapsibleGroup(
        "Experiment",
        [
            Button(0, 0, 0, 0, "Load reference layout", cb_load_reference_layout),
            NumericField("Seed", lambda: sim_seed, set_seed_from_field, fmt="{:.0f}"),
            Button(0, 0, 0, 0, "New sample", cb_new_sample),
            Button(0, 0, 0, 0, "Reseed random", cb_reseed_random),
            NumericField("Draw rays", lambda: 1 if draw_rays_enabled else 0, set_draw_from_field, fmt="{:.0f}"),
            NumericField("Max rays", lambda: max_rays, set_max_rays_from_field, fmt="{:.0f}"),
            NumericField("Fiber rays", lambda: fiber_num_rays, set_fiber_rays_from_field, fmt="{:.0f}"),
        ],
        expanded=True,
    ),
    CollapsibleGroup(
        "Sweep",
        [
            NumericField("Base seed", lambda: sweep_base_seed, set_sweep_seed_from_field, fmt="{:.0f}"),
            NumericField("Start", lambda: sweep_start, set_sweep_start_from_field, fmt="{:.6g}"),
            NumericField("Stop", lambda: sweep_stop, set_sweep_stop_from_field, fmt="{:.6g}"),
            NumericField("Step", lambda: sweep_step, set_sweep_step_from_field, fmt="{:.6g}"),
            NumericField("Rays cap", lambda: sweep_rays_cap, set_sweep_rays_from_field, fmt="{:.0f}"),
            Button(0, 0, 0, 0, "Run sweep", cb_run_sweep),
        ],
        expanded=False,
    ),
    CollapsibleGroup(
        "Sources",
        [
            Button(0, 0, 0, 0, "Add Fiber", cb_add_fiber),
            Button(0, 0, 0, 0, "Clear Fiber", cb_clear_fiber),
            Button(0, 0, 0, 0, "Add Beam", cb_add_beam),
            Button(0, 0, 0, 0, "Clear Beams", cb_clear_beams),
        ],
        expanded=True,
    ),
    CollapsibleGroup(
        "Reflectors",
        [
            Button(0, 0, 0, 0, "Add Mirror", cb_add_mirror),
            Button(0, 0, 0, 0, "Clear Mirrors", cb_clear_mirrors),
            Button(0, 0, 0, 0, "Add LensedMirror", cb_add_lensed_mirror),
            Button(0, 0, 0, 0, "Clear Lensed", cb_clear_lensed_mirrors),
        ],
        expanded=True,
    ),
    CollapsibleGroup(
        "Optics",
        [
            Button(0, 0, 0, 0, "Add Lens", cb_add_lens),
            Button(0, 0, 0, 0, "Clear Lenses", cb_clear_lenses),
            Button(0, 0, 0, 0, "Add Media Interface", cb_add_media),
            Button(0, 0, 0, 0, "Clear Media Interface", cb_clear_media_interfaces),
            Button(0, 0, 0, 0, "Add Media Polygon", cb_add_media_poly),
            Button(0, 0, 0, 0, "Clear Media Polygons", cb_clear_media_polygons),
        ],
        expanded=True,
    ),
    CollapsibleGroup(
        "Sensors",
        [
            Button(0, 0, 0, 0, "Add Detector", cb_add_detector),
            Button(0, 0, 0, 0, "Clear Detectors", cb_clear_detectors),
        ],
        expanded=True,
    ),
    properties_group,
]


def _emit_rays(rng, fiber_rays_override: int | None = None, cap: int | None = None):
    """Emit rays from all sources.

    - If there are Beam sources, emit from all beams.
    - If there are Fiber sources, emit from all fibers as well.
    - Normalize total emitted power to 1.0 (so IL is stable vs ray count).
    - Optionally cap total rays for performance.
    """
    beams = [o for o in scene.objects if isinstance(o, Beam)]
    fibers = [o for o in scene.objects if isinstance(o, FiberSource)]

    rays = []
    ray_id = 0

    for b in beams:
        r = b.emit(ray_id_start=ray_id)
        rays.extend(r)
        ray_id += len(r)

    for f in fibers:
        n = int(fiber_rays_override) if fiber_rays_override is not None else int(fiber_num_rays)
        r = f.emit(num_rays=n, ray_id_start=ray_id, rng=rng, um_per_px=interaction.um_per_px)
        rays.extend(r)
        ray_id += len(r)

    if cap is not None:
        cap_i = int(max(0, cap))
        if cap_i and len(rays) > cap_i:
            rays = rays[:cap_i]

    # Normalize total power to 1.0 for stable IL
    p_emit = sum(getattr(r, "power", 1.0) for r in rays)
    if p_emit > 0:
        s = 1.0 / p_emit
        for r in rays:
            r.power = getattr(r, "power", 1.0) * s

    return rays


def _format_db(il_db: float) -> str:
    if math.isinf(il_db):
        return "∞"
    return f"{il_db:.2f}"


def _seg_center(obj):
    return Vector((obj.p1.x + obj.p2.x) * 0.5, (obj.p1.y + obj.p2.y) * 0.5)


def _seg_len_px(obj):
    return (obj.p2 - obj.p1).length()


def _seg_angle_deg(obj):
    d = obj.p2 - obj.p1
    return math.degrees(math.atan2(d.y, d.x))


def _set_seg_center(obj, cx_px, cy_px):
    c = _seg_center(obj)
    dx = cx_px - c.x
    dy = cy_px - c.y
    obj.p1 = Vector(obj.p1.x + dx, obj.p1.y + dy)
    obj.p2 = Vector(obj.p2.x + dx, obj.p2.y + dy)


def _set_seg_len_px(obj, length_px):
    length_px = max(1e-3, float(length_px))
    c = _seg_center(obj)
    a = math.radians(_seg_angle_deg(obj))
    dx = math.cos(a) * (length_px * 0.5)
    dy = math.sin(a) * (length_px * 0.5)
    obj.p1 = Vector(c.x - dx, c.y - dy)
    obj.p2 = Vector(c.x + dx, c.y + dy)


def _set_seg_angle_deg(obj, ang_deg):
    c = _seg_center(obj)
    L = _seg_len_px(obj)
    a = math.radians(float(ang_deg))
    dx = math.cos(a) * (L * 0.5)
    dy = math.sin(a) * (L * 0.5)
    obj.p1 = Vector(c.x - dx, c.y - dy)
    obj.p2 = Vector(c.x + dx, c.y + dy)


def build_properties(sel):
    items = []

    um = float(interaction.um_per_px) if interaction.um_per_px else 1.0

    # Background (when nothing selected)
    if sel is None:
        items.append(NumericField("BG n", lambda: scene.medium.n, lambda v: setattr(scene.medium, "n", float(v)), fmt="{:.4f}"))
        items.append(NumericField("BG alpha", lambda: scene.medium.alpha_per_um, lambda v: setattr(scene.medium, "alpha_per_um", float(v)), unit="1/µm", fmt="{:.6g}"))
        items.append(NumericField("Snap", lambda: 1 if interaction.snap_enabled else 0, lambda v: setattr(interaction, "snap_enabled", bool(int(round(v)))), fmt="{:.0f}"))
        return items

    # Media polygon
    if isinstance(sel, MediaPolygon):
        # Layer / duplication helpers
        def _dup_media():
            if len(sel.points) < 3:
                return
            offs = Vector(20, 20)
            pts = [Vector(p.x + offs.x, p.y + offs.y) for p in sel.points]
            newp = MediaPolygon(pts, n=float(sel.medium.n), alpha_per_um=float(sel.medium.alpha_per_um))
            scene.add(newp)
            interaction.selected = newp
            interaction.poly_vertex_index = 0

        def _bring_forward():
            # Move this polygon later among polygons -> higher priority
            polys = [i for i, o in enumerate(scene.objects) if isinstance(o, MediaPolygon)]
            if not polys:
                return
            idx = scene.objects.index(sel)
            # find next polygon index after current
            next_poly = None
            for j in polys:
                if j > idx:
                    next_poly = j
                    break
            if next_poly is None:
                return
            scene.objects[idx], scene.objects[next_poly] = scene.objects[next_poly], scene.objects[idx]

        def _send_backward():
            polys = [i for i, o in enumerate(scene.objects) if isinstance(o, MediaPolygon)]
            if not polys:
                return
            idx = scene.objects.index(sel)
            prev_poly = None
            for j in reversed(polys):
                if j < idx:
                    prev_poly = j
                    break
            if prev_poly is None:
                return
            scene.objects[idx], scene.objects[prev_poly] = scene.objects[prev_poly], scene.objects[idx]

        # Vertex editing
        def _clamp_vertex_index(v: int):
            if not sel.points:
                interaction.poly_vertex_index = 0
                return
            interaction.poly_vertex_index = max(0, min(int(v), len(sel.points) - 1))

        def _prev_vertex():
            if not sel.points:
                return
            interaction.poly_vertex_index = (interaction.poly_vertex_index - 1) % len(sel.points)

        def _next_vertex():
            if not sel.points:
                return
            interaction.poly_vertex_index = (interaction.poly_vertex_index + 1) % len(sel.points)

        def _add_vertex():
            pts = sel.points
            if len(pts) < 2:
                return
            i = interaction.poly_vertex_index
            a = pts[i]
            b = pts[(i + 1) % len(pts)]
            mid = Vector((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)
            pts.insert(i + 1, mid)
            interaction.poly_vertex_index = i + 1

        def _del_vertex():
            pts = sel.points
            if len(pts) <= 3:
                return
            i = interaction.poly_vertex_index
            pts.pop(i)
            interaction.poly_vertex_index = max(0, min(interaction.poly_vertex_index, len(pts) - 1))

        def _get_vx():
            if not sel.points:
                return 0.0
            i = max(0, min(interaction.poly_vertex_index, len(sel.points) - 1))
            return sel.points[i].x * um

        def _set_vx(vv):
            if not sel.points:
                return
            i = max(0, min(interaction.poly_vertex_index, len(sel.points) - 1))
            sel.points[i].x = float(vv) / um

        def _get_vy():
            if not sel.points:
                return 0.0
            i = max(0, min(interaction.poly_vertex_index, len(sel.points) - 1))
            return sel.points[i].y * um

        def _set_vy(vv):
            if not sel.points:
                return
            i = max(0, min(interaction.poly_vertex_index, len(sel.points) - 1))
            sel.points[i].y = float(vv) / um

        items.append(NumericField("n", lambda: sel.medium.n, lambda v: setattr(sel.medium, "n", float(v)), fmt="{:.4f}"))
        items.append(NumericField("alpha", lambda: sel.medium.alpha_per_um, lambda v: setattr(sel.medium, "alpha_per_um", float(v)), unit="1/µm", fmt="{:.6g}"))
        items.append(NumericField("V#", lambda: (interaction.poly_vertex_index + 1) if sel.points else 0,
                                  lambda v: _clamp_vertex_index(int(round(v)) - 1), fmt="{:.0f}"))
        items.append(NumericField("Vx", _get_vx, _set_vx, unit="µm", fmt="{:.2f}"))
        items.append(NumericField("Vy", _get_vy, _set_vy, unit="µm", fmt="{:.2f}"))
        items.append(Button(0, 0, 0, 0, "Prev vertex", _prev_vertex))
        items.append(Button(0, 0, 0, 0, "Next vertex", _next_vertex))
        items.append(Button(0, 0, 0, 0, "Add vertex", _add_vertex))
        items.append(Button(0, 0, 0, 0, "Delete vertex", _del_vertex))
        items.append(Button(0, 0, 0, 0, "Duplicate media", _dup_media))
        items.append(Button(0, 0, 0, 0, "Bring forward", _bring_forward))
        items.append(Button(0, 0, 0, 0, "Send backward", _send_backward))
        return items

    # Media interface
    if isinstance(sel, MediaInterface):
        items.append(NumericField("n1", lambda: sel.n1, lambda v: setattr(sel, "n1", float(v)), fmt="{:.4f}"))
        items.append(NumericField("n2", lambda: sel.n2, lambda v: setattr(sel, "n2", float(v)), fmt="{:.4f}"))

    # Segment-like objects: center, length, angle
    if hasattr(sel, "p1") and hasattr(sel, "p2"):
        items.insert(0, NumericField("Center X", lambda: _seg_center(sel).x * um, lambda v: _set_seg_center(sel, float(v) / um, _seg_center(sel).y), unit="µm", fmt="{:.2f}"))
        items.insert(1, NumericField("Center Y", lambda: _seg_center(sel).y * um, lambda v: _set_seg_center(sel, _seg_center(sel).x, float(v) / um), unit="µm", fmt="{:.2f}"))
        items.insert(2, NumericField("Length", lambda: _seg_len_px(sel) * um, lambda v: _set_seg_len_px(sel, float(v) / um), unit="µm", fmt="{:.2f}"))
        items.insert(3, NumericField("Angle", lambda: _seg_angle_deg(sel), lambda v: _set_seg_angle_deg(sel, float(v)), unit="deg", fmt="{:.2f}"))

    # Special params
    if isinstance(sel, Lens):
        items.append(NumericField("f", lambda: sel.f * um, lambda v: setattr(sel, "f", float(v) / um), unit="µm", fmt="{:.2f}"))
    if isinstance(sel, LensedMirror):
        items.append(NumericField("bulge", lambda: sel.bulge * um, lambda v: setattr(sel, "bulge", float(v) / um), unit="µm", fmt="{:.2f}"))
    if isinstance(sel, Beam):
        items.append(NumericField("spread", lambda: sel.spread_deg, lambda v: setattr(sel, "spread_deg", float(v)), unit="deg", fmt="{:.2f}"))
        items.append(NumericField("ang_samples", lambda: sel.angle_samples, lambda v: setattr(sel, "angle_samples", int(max(1, round(v)))), fmt="{:.0f}"))
        items.append(NumericField("spacing", lambda: sel.pos_spacing_px * um, lambda v: setattr(sel, "pos_spacing_px", float(v) / um), unit="µm", fmt="{:.2f}"))
        items.append(NumericField("power", lambda: sel.total_power, lambda v: setattr(sel, "total_power", float(v)), fmt="{:.4f}"))

    return items


last_selected = None


running = True
# Sidebar scrolling
sidebar_scroll = 0.0
sidebar_content_height = 0.0
sidebar_max_scroll = 0.0
SIDEBAR_SCROLL_STEP = 40  # px per wheel notch

while running:
    mx, my = pygame.mouse.get_pos()
    mouse = Vector(mx, my)

    sidebar_area = pygame.Rect(0, UI_BAR_H, SIDEBAR_W, HEIGHT - UI_BAR_H)
    canvas_area = pygame.Rect(SIDEBAR_W, UI_BAR_H, WIDTH - SIDEBAR_W, HEIGHT - UI_BAR_H)

    # Clamp sidebar scroll from previous frame
    sidebar_scroll = max(0.0, min(sidebar_scroll, sidebar_max_scroll))

    # Update properties panel when selection changes
    if interaction.selected is not last_selected:
        # Deactivate any active field when selection changes
        if interaction.active_field is not None:
            interaction.active_field.active = False
            interaction.active_field = None

        # Reset vertex index when selecting a different polygon
        if isinstance(interaction.selected, MediaPolygon):
            interaction.poly_vertex_index = 0
        properties_group.buttons = build_properties(interaction.selected)
        last_selected = interaction.selected

    # Layout sidebar groups
    y_cursor = UI_BAR_H + SIDEBAR_PAD - sidebar_scroll
    x_cursor = SIDEBAR_PAD
    group_w = SIDEBAR_W - 2 * SIDEBAR_PAD
    for g in groups:
        if g is properties_group:
            y_cursor = g.layout(x_cursor, y_cursor, group_w, btn_h=GROUP_FIELD_H)
        else:
            y_cursor = g.layout(x_cursor, y_cursor, group_w)
        y_cursor += 8

    # Update scroll limits based on total sidebar content height
    sidebar_content_height = max(0.0, (y_cursor + sidebar_scroll) - (UI_BAR_H + SIDEBAR_PAD))
    sidebar_max_scroll = max(0.0, sidebar_content_height - sidebar_area.height + SIDEBAR_PAD)
    sidebar_scroll = max(0.0, min(sidebar_scroll, sidebar_max_scroll))

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        # Sidebar groups (capture focus for fields)
        for g in groups:
            focus_item = g.handle_event(e)
            if focus_item is not None:
                if interaction.active_field is not None and interaction.active_field is not focus_item:
                    interaction.active_field.active = False
                interaction.active_field = focus_item

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_c:
                rng_manager.set_seed(_effective_seed())
                rays_tmp = _emit_rays(rng_manager.rng(), cap=max_rays)
                if rays_tmp:
                    ref_ray = rays_tmp[len(rays_tmp) // 2]
                    hits = trace_hits(ref_ray, scene, max_hits=1)
                    if len(hits) == 1:
                        d1_px = (hits[0] - ref_ray.pos).length()
                        if d1_px > 1e-9:
                            interaction.um_per_px = interaction.ref_d1_um / d1_px

            if e.key == pygame.K_s:
                interaction.snap_enabled = not interaction.snap_enabled

            if e.key == pygame.K_ESCAPE:
                # Cancel polygon creation
                if interaction.add_mode == "media_poly":
                    interaction.add_mode = None
                    interaction.poly_points = []
                    interaction.current_pos = None

        if e.type == pygame.MOUSEWHEEL:
            # Sidebar scrolling: mouse wheel scrolls the sidebar when hovered
            if sidebar_area.collidepoint((mx, my)) and sidebar_max_scroll > 0:
                sidebar_scroll -= e.y * SIDEBAR_SCROLL_STEP
                sidebar_scroll = max(0.0, min(sidebar_scroll, sidebar_max_scroll))
                continue

            sel = interaction.selected
            if isinstance(sel, LensedMirror):
                delta = e.y * BULGE_WHEEL_STEP
                sel.adjust_bulge(delta, max_abs=BULGE_WHEEL_MAX_ABS)

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                exit_btn_rect = pygame.Rect(WIDTH - 50, 15, 35, 35)
                if exit_btn_rect.collidepoint((mx, my)):
                    running = False
                    continue

            if not canvas_area.collidepoint((mx, my)):
                continue

            # Polygon creation: left click adds vertex, right click finishes
            if interaction.add_mode == "media_poly":
                if e.button == 1:
                    p = snap_point(mouse, scene, enabled=interaction.snap_enabled, extra_points=interaction.poly_points)
                    interaction.poly_points.append(p)
                    interaction.current_pos = p
                    continue
                if e.button == 3:
                    if len(interaction.poly_points) >= 3:
                        scene.add(MediaPolygon(interaction.poly_points, n=1.5, alpha_per_um=0.0))
                    interaction.add_mode = None
                    interaction.poly_points = []
                    interaction.current_pos = None
                    continue

            if e.button == 3:
                # Right-click delete
                for obj in list(scene.objects):
                    hit = False
                    if hasattr(obj, "vertex_hit") and obj.vertex_hit(mouse) is not None:
                        hit = True
                    elif hasattr(obj, "contains_point") and obj.contains_point(mouse):
                        hit = True
                    if hit:
                        if interaction.selected is obj:
                            interaction.selected = None
                        scene.remove(obj)
                        break

            elif e.button == 1:
                # Add-mode: start preview (segment tools)
                if interaction.add_mode:
                    if interaction.add_mode == "fiber":
                        p = snap_point(mouse, scene, enabled=interaction.snap_enabled)
                        fiber = FiberSource(p.x, p.y)
                        scene.add(fiber)
                        scene.add(fiber.facet)
                        interaction.add_mode = None
                        continue

                    interaction.start_pos = snap_point(mouse, scene, enabled=interaction.snap_enabled)
                    interaction.current_pos = interaction.start_pos
                    continue

                interaction.dragging = None
                interaction.drag_mode = None
                interaction.last_mouse = mouse

                clicked_obj = None

                for obj in reversed(scene.objects):
                    # MediaPolygon: vertex drag or move
                    if isinstance(obj, MediaPolygon):
                        vi = obj.vertex_hit(mouse, radius=10.0)
                        if vi is not None:
                            clicked_obj = obj
                            interaction.dragging = obj
                            interaction.drag_mode = ("vertex", vi)
                            break
                        if obj.contains_point(mouse):
                            clicked_obj = obj
                            interaction.dragging = obj
                            interaction.drag_mode = "move"
                            break
                        continue

                    # Non-segment objects (fiber, etc.)
                    if not hasattr(obj, "p1") or not hasattr(obj, "p2"):
                        if hasattr(obj, "contains_point") and obj.contains_point(mouse):
                            clicked_obj = obj
                            interaction.dragging = obj
                            interaction.drag_mode = "move"
                            break
                        continue

                    # endpoint resize
                    if (mouse - obj.p1).length() < 10:
                        clicked_obj = obj
                        interaction.dragging = obj
                        interaction.drag_mode = "p1"
                        break
                    if (mouse - obj.p2).length() < 10:
                        clicked_obj = obj
                        interaction.dragging = obj
                        interaction.drag_mode = "p2"
                        break

                    # segment drag: rotate (SHIFT = move)
                    if hasattr(obj, "contains_point") and obj.contains_point(mouse):
                        clicked_obj = obj
                        interaction.dragging = obj
                        interaction.drag_mode = "rotate" if pygame.key.get_mods() & pygame.KMOD_SHIFT else "move"
                        break

                interaction.selected = clicked_obj

        if e.type == pygame.MOUSEMOTION:
            if interaction.add_mode and interaction.start_pos:
                interaction.current_pos = snap_point(mouse, scene, enabled=interaction.snap_enabled)
            if interaction.add_mode == "media_poly":
                interaction.current_pos = snap_point(mouse, scene, enabled=interaction.snap_enabled, extra_points=interaction.poly_points)

            if interaction.dragging and interaction.last_mouse:
                obj = interaction.dragging

                if interaction.drag_mode == "move":
                    dx = mouse.x - interaction.last_mouse.x
                    dy = mouse.y - interaction.last_mouse.y
                    if hasattr(obj, "move"):
                        obj.move(dx, dy)

                elif interaction.drag_mode == "p1":
                    obj.p1 = snap_point(mouse, scene, enabled=interaction.snap_enabled)

                elif interaction.drag_mode == "p2":
                    obj.p2 = snap_point(mouse, scene, enabled=interaction.snap_enabled)

                elif interaction.drag_mode == "rotate":
                    cx = (obj.p1.x + obj.p2.x) / 2
                    cy = (obj.p1.y + obj.p2.y) / 2
                    half_len = (obj.p2 - obj.p1).length() / 2
                    angle = math.atan2(my - cy, mx - cx)
                    p1 = Vector(cx - math.cos(angle) * half_len,
                                cy - math.sin(angle) * half_len)
                    p2 = Vector(cx + math.cos(angle) * half_len,
                                cy + math.sin(angle) * half_len)
                    obj.p1 = snap_point(p1, scene, enabled=interaction.snap_enabled)
                    obj.p2 = snap_point(p2, scene, enabled=interaction.snap_enabled)

                elif isinstance(interaction.drag_mode, tuple) and interaction.drag_mode[0] == "vertex":
                    idx = interaction.drag_mode[1]
                    obj.points[idx] = snap_point(mouse, scene, enabled=interaction.snap_enabled, extra_points=obj.points)

                interaction.last_mouse = mouse

        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if interaction.add_mode and interaction.start_pos and interaction.current_pos:
                a = interaction.start_pos
                b = interaction.current_pos
                if (b - a).length() > 5:
                    if interaction.add_mode == "mirror":
                        scene.add(Mirror(Vector(a.x, a.y), Vector(b.x, b.y)))
                    elif interaction.add_mode == "lensed_mirror":
                        scene.add(LensedMirror(Vector(a.x, a.y), Vector(b.x, b.y), bulge=40.0))
                    elif interaction.add_mode == "lens":
                        scene.add(Lens(Vector(a.x, a.y), Vector(b.x, b.y), f=140))
                    elif interaction.add_mode == "detector":
                        scene.add(Detector(Vector(a.x, a.y), Vector(b.x, b.y)))
                    elif interaction.add_mode == "media":
                        scene.add(MediaInterface(Vector(a.x, a.y), Vector(b.x, b.y), n1=1.0, n2=1.5))
                    elif interaction.add_mode == "beam":
                        scene.add(Beam(Vector(a.x, a.y), Vector(b.x, b.y),
                                       spread_deg=BEAM_DEFAULT_SPREAD_DEG,
                                       pos_spacing_px=BEAM_DEFAULT_POS_SPACING_PX,
                                       angle_samples=BEAM_DEFAULT_ANGLE_SAMPLES,
                                       total_power=1.0))

                interaction.start_pos = None
                interaction.current_pos = None
                interaction.add_mode = None

            interaction.dragging = None
            interaction.drag_mode = None
            interaction.last_mouse = None

    # --- draw ---
    screen.fill(BG)

    # Modern top bar
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, UI_BAR_H))
    pygame.draw.line(screen, SIDEBAR_BORDER, (0, UI_BAR_H - 1), (WIDTH, UI_BAR_H - 1), 2)

    title_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 30, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 16)

    title = title_font.render("Optical Ray Tracer", True, UI_TEXT_PRIMARY)
    subtitle = subtitle_font.render("Professional Simulation Environment", True, (168, 85, 247))

    screen.blit(title, (28, 14))
    screen.blit(subtitle, (29, 55))

    hints_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 17)
    hint_text = "Drag to move  •  SHIFT+drag rotate  •  Right-click delete  •  C calibrate  •  S snap  •  Wheel bulge"
    hint_surf = hints_font.render(hint_text, True, (170, 180, 200))
    screen.blit(hint_surf, (SIDEBAR_W + 20, 55))

    # Exit button
    exit_btn_rect = pygame.Rect(WIDTH - 50, 15, 35, 35)
    exit_hover = exit_btn_rect.collidepoint((mx, my))
    exit_color = (168, 85, 247) if exit_hover else (100, 110, 130)
    pygame.draw.rect(screen, exit_color, exit_btn_rect, border_radius=8)
    pygame.draw.rect(screen, (150, 160, 180), exit_btn_rect, 2, border_radius=8)
    pygame.draw.line(screen, (240, 240, 240),
                     (exit_btn_rect.x + 9, exit_btn_rect.y + 9),
                     (exit_btn_rect.x + 26, exit_btn_rect.y + 26), 2)
    pygame.draw.line(screen, (240, 240, 240),
                     (exit_btn_rect.x + 26, exit_btn_rect.y + 9),
                     (exit_btn_rect.x + 9, exit_btn_rect.y + 26), 2)

    # Sidebar
    pygame.draw.rect(screen, SIDEBAR_BG, sidebar_area)
    pygame.draw.line(screen, SIDEBAR_BORDER, (SIDEBAR_W, UI_BAR_H), (SIDEBAR_W, HEIGHT), 2)

    screen.set_clip(sidebar_area)
    for g in groups:
        g.draw(screen, font)
    screen.set_clip(None)

    # Sidebar scrollbar (visible when content overflows)
    if sidebar_max_scroll > 0 and sidebar_content_height > 0:
        track = pygame.Rect(SIDEBAR_W - 10, UI_BAR_H + 6, 6, sidebar_area.height - 12)
        # Thumb size proportional to viewport/content
        ratio = sidebar_area.height / max(sidebar_content_height, sidebar_area.height)
        thumb_h = max(24, int(track.height * ratio))
        if sidebar_max_scroll > 0:
            thumb_y = int(track.y + (sidebar_scroll / sidebar_max_scroll) * (track.height - thumb_h))
        else:
            thumb_y = track.y
        thumb = pygame.Rect(track.x, thumb_y, track.w, thumb_h)
        pygame.draw.rect(screen, (90, 100, 120), track, border_radius=3)
        pygame.draw.rect(screen, (168, 85, 247), thumb, border_radius=3)

    # Canvas
    screen.set_clip(canvas_area)
    draw_grid(screen)

    # Reset detectors each frame
    for o in scene.objects:
        if isinstance(o, Detector):
            o.reset()

    # Emit + trace rays
    rng_manager.set_seed(_effective_seed())
    rays = _emit_rays(rng_manager.rng(), cap=max_rays)
    p_emitted = sum(getattr(r, "power", 1.0) for r in rays)
    trace_rays(
        rays,
        scene,
        screen if draw_rays_enabled else None,
        um_per_px=interaction.um_per_px,
        draw=draw_rays_enabled,
    )

    # Draw objects
    for o in scene.objects:
        if hasattr(o, "draw"):
            o.draw(screen)

    # Detector labels
    for o in scene.objects:
        if isinstance(o, Detector):
            cx = (o.p1.x + o.p2.x) / 2
            cy = (o.p1.y + o.p2.y) / 2
            label = font_small.render(f"{o.count} rays", True, (20, 20, 30))
            label_rect = label.get_rect(topleft=(cx + 6, cy + 6))
            label_rect.inflate_ip(8, 4)
            pygame.draw.rect(screen, (200, 200, 220), label_rect, border_radius=4)
            pygame.draw.rect(screen, (150, 150, 170), label_rect, 1, border_radius=4)
            screen.blit(label, (cx + 6, cy + 6))

    # Preview while adding segment tools
    if interaction.add_mode and interaction.start_pos and interaction.current_pos:
        preview_color = (125, 211, 252)
        if interaction.add_mode == "lens":
            preview_color = (134, 239, 172)
        elif interaction.add_mode == "detector":
            preview_color = (248, 113, 113)
        elif interaction.add_mode == "beam":
            preview_color = (167, 139, 250)
        pygame.draw.line(screen, preview_color, interaction.start_pos.tuple(), interaction.current_pos.tuple(), 2)

    # Preview while drawing a media polygon (no crash for <2 points)
    if interaction.add_mode == "media_poly":
        pts = interaction.poly_points
        if len(pts) == 1 and interaction.current_pos:
            pygame.draw.circle(screen, (34, 197, 94), pts[0].tuple(), 4)
            pygame.draw.line(screen, (34, 197, 94), pts[0].tuple(), interaction.current_pos.tuple(), 2)
        elif len(pts) >= 2:
            pygame.draw.lines(screen, (34, 197, 94), False, [p.tuple() for p in pts], 2)
            if interaction.current_pos:
                pygame.draw.line(screen, (34, 197, 94), pts[-1].tuple(), interaction.current_pos.tuple(), 2)
            for p in pts:
                pygame.draw.circle(screen, (167, 139, 250), p.tuple(), 5)

    screen.set_clip(None)

    # Hover tooltip
    hover_info = None
    for o in scene.objects:
        if hasattr(o, "contains_point") and o.contains_point(mouse):
            if hasattr(o, "get_params_str"):
                hover_info = o.get_params_str()
                break

    if hover_info:
        tooltip_font = font_small
        line_surfaces = [tooltip_font.render(line, True, (255, 255, 255)) for line in hover_info]
        max_width = max(surf.get_width() for surf in line_surfaces)
        total_height = sum(surf.get_height() for surf in line_surfaces)
        tooltip_rect = pygame.Rect(mx + 10, my + 10, max_width + 16, total_height + 8)
        pygame.draw.rect(screen, (100, 100, 100), tooltip_rect, border_radius=4)
        pygame.draw.rect(screen, (150, 150, 150), tooltip_rect, 1, border_radius=4)
        y_offset = tooltip_rect.y + 4
        for surf in line_surfaces:
            screen.blit(surf, (tooltip_rect.x + 8, y_offset))
            y_offset += surf.get_height()

    # --- Left overlay (stats) ---
    overlay_lines = [
        f"UM_PER_PX = {interaction.um_per_px:.6f} µm/px (press C to calibrate using {interaction.ref_d1_um:.0f} µm)",
        f"Background: n = {scene.medium.n:.4f}  |  alpha = {scene.medium.alpha_per_um:.6g} 1/µm",
        f"Snap: {'ON' if interaction.snap_enabled else 'OFF'} (press S)",
        f"Seed = {sim_seed}  |  sample = {sim_sample_offset}  |  effective = {_effective_seed()}",
        f"Draw rays = {'ON' if draw_rays_enabled else 'OFF'}  |  Max rays = {max_rays}  |  Fiber rays = {fiber_num_rays}",
        f"Rays emitted = {len(rays)}  |  P_emitted = {p_emitted:.4f}",
    ]

    # Sweep status
    tgt = _sweep_target_from_selection()
    if tgt is not None:
        overlay_lines.append(f"Sweep target: {tgt[0]}  (set Start/Stop/Step in the Sweep panel)")
    if template_last_msg:
        overlay_lines.append(template_last_msg)
    if sweep_last_msg:
        overlay_lines.append(sweep_last_msg)

    sel = interaction.selected
    if isinstance(sel, LensedMirror):
        overlay_lines.append(f"Selected: LensedMirror  bulge={sel.bulge:.2f}px")
    elif isinstance(sel, Lens):
        overlay_lines.append(f"Selected: Lens  f={sel.f:.2f}px")
    elif isinstance(sel, Beam):
        overlay_lines.append(f"Selected: Beam  spread=±{sel.spread_deg:.1f}°  angles={sel.angle_samples}  spacing={sel.pos_spacing_px:.1f}px")
    elif isinstance(sel, Detector):
        overlay_lines.append("Selected: Detector")
    elif isinstance(sel, Mirror):
        overlay_lines.append("Selected: Mirror")
    elif isinstance(sel, MediaPolygon):
        overlay_lines.append(f"Selected: MediaPolygon  n={sel.medium.n:.4f} alpha={sel.medium.alpha_per_um:.6g} 1/µm")
    elif isinstance(sel, MediaInterface):
        overlay_lines.append(f"Selected: MediaInterface  n1={sel.n1:.4f} n2={sel.n2:.4f}")

    detectors = [o for o in scene.objects if isinstance(o, Detector)]
    if detectors:
        union_ids = set()
        union_power = 0.0

        overlay_lines.append("--- Detectors ---")
        for i, d in enumerate(detectors, start=1):
            p_det = d.power_sum
            ratio = p_det / p_emitted if p_emitted > 0 else 0.0
            il_db = float("inf") if ratio <= 0 else -10.0 * math.log10(ratio)
            overlay_lines.append(f"Detector {i}: {d.count} rays | P={p_det:.4f} | IL={_format_db(il_db)} dB")

            for rid, pw in d.power_by_ray_id.items():
                if rid not in union_ids:
                    union_ids.add(rid)
                    union_power += pw

        ratio_u = union_power / p_emitted if p_emitted > 0 else 0.0
        il_u = float("inf") if ratio_u <= 0 else -10.0 * math.log10(ratio_u)
        overlay_lines.append(f"Total unique detected: {len(union_ids)} | P={union_power:.4f} | IL={_format_db(il_u)} dB")

    # Reference ray tracker (angles + medium boundary transitions)
    if rays:
        ref_ray = rays[len(rays) // 2]
        evs = trace_reference_events(ref_ray, scene, um_per_px=float(interaction.um_per_px) if interaction.um_per_px else 1.0, max_events=8)

        def _adir(v: Vector) -> float:
            return math.degrees(math.atan2(v.y, v.x))

        overlay_lines.append("--- Reference ray ---")
        overlay_lines.append(f"θ0 = {_adir(ref_ray.dir):.2f}°")
        if not evs:
            overlay_lines.append("No hits/boundaries for reference ray.")
        else:
            for k, eev in enumerate(evs, start=1):
                a_in = _adir(eev["dir_in"])
                a_out = _adir(eev["dir_out"])
                if eev["type"] == "boundary":
                    tir = " (TIR)" if eev.get("did_reflect") else ""
                    overlay_lines.append(
                        f"B{k}: {eev.get('m1','')}→{eev.get('m2','')} (n {eev['n1']:.3f}→{eev['n2']:.3f}) | θ {a_in:.1f}°→{a_out:.1f}°{tir}"
                    )
                else:
                    overlay_lines.append(
                        f"{eev.get('name','Element')} | θ {a_in:.1f}°→{a_out:.1f}°"
                    )

    draw_overlay_lines(screen, font, overlay_lines, x=SIDEBAR_W + 14, y=UI_BAR_H + 10)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
