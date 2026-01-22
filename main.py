import pygame
import math

from config import *
from core.vector import Vector
from components.mirror import Mirror
from components.lensed_mirror import LensedMirror
from components.media_interface import MediaInterface
from components.lens import Lens
from components.detector import Detector
from components.sources.beam import Beam
from components.sources.fiber import FiberSource
from simulation.scene import Scene
from simulation.tracer import trace_rays, trace_hits
from ui.grid import draw_grid
from ui.interaction import InteractionState
from ui.button import Button
from ui.collapsible_group import CollapsibleGroup
from ui.overlay import draw_overlay_lines
from file_conversion.input_file import load_elements
from file_conversion.extract_param_to_file import save_scene


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", FONT_SIZE)
font_small = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", FONT_SMALL_SIZE)


# --- Scene / state ---
scene = Scene()
scene.medium.alpha_per_um = ALPHA_PER_UM_DEFAULT

interaction = InteractionState()
interaction.um_per_px = UM_PER_PX_DEFAULT
interaction.ref_d1_um = REF_D1_UM_DEFAULT

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


def cb_clear_media():
    scene.clear_by_type(MediaInterface)

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

def cb_load_scene():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename(
        title="Load optical scene",
        filetypes=[
            ("Scene files", "*.json *.yaml *.yml"),
            ("JSON files", "*.json"),
            ("YAML files", "*.yaml *.yml"),
        ],
    )

    if not file_path:
        return

    try:
        elements = load_elements(file_path)

        scene.clear()
        for el in elements:
            scene.add(el)

            # FiberSource special case (facet)
            if isinstance(el, FiberSource):
                scene.add(el.facet)

    except Exception as e:
        print(f"[ERROR] Failed to load scene: {e}")

def cb_save_scene():
    import tkinter as tk
    from tkinter import filedialog


    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.asksaveasfilename(
        title="Save optical scene",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
    )

    if not file_path:
        return

    save_scene(scene, file_path)


# Sidebar: expandable tool groups (supervisor suggestion)
groups = [
    CollapsibleGroup(
        "Scene",
        [
            Button(0, 0, 0, 0, "Load Scene", cb_load_scene),
            Button(0, 0, 0, 0, "Save Scene", cb_save_scene),
            
        ],
        expanded=True,
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
            Button(0, 0, 0, 0, "Clear Media Interface", cb_clear_media),
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
]


def _emit_rays():
    beams = [o for o in scene.objects if isinstance(o, Beam)]
    fibers = [o for o in scene.objects if isinstance(o, FiberSource)]
    rays = []
    ray_id = 0
    if beams:
        for b in beams:
            r = b.emit(ray_id_start=ray_id)
            rays.extend(r)
            ray_id += len(r)
    elif fibers:
        fiber = fibers[0]  # Assume one fiber for simplicity
        rays = fiber.emit(num_rays=FIBER_NUM_RAYS, ray_id_start=0)
    return rays


def _format_db(il_db: float) -> str:
    if math.isinf(il_db):
        return "∞"
    return f"{il_db:.2f}"


running = True
while running:
    mx, my = pygame.mouse.get_pos()
    mouse = Vector(mx, my)

    sidebar_area = pygame.Rect(0, UI_BAR_H, SIDEBAR_W, HEIGHT - UI_BAR_H)
    canvas_area = pygame.Rect(SIDEBAR_W, UI_BAR_H, WIDTH - SIDEBAR_W, HEIGHT - UI_BAR_H)

    # Layout the sidebar groups each frame (they can expand/collapse)
    y_cursor = UI_BAR_H + SIDEBAR_PAD
    x_cursor = SIDEBAR_PAD
    group_w = SIDEBAR_W - 2 * SIDEBAR_PAD
    for g in groups:
        y_cursor = g.layout(x_cursor, y_cursor, group_w)
        y_cursor += 8

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        # Sidebar groups
        for g in groups:
            g.handle_event(e)

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_c:
                # Calibrate µm/px using first hit of the reference ray.
                rays_tmp = _emit_rays()
                if rays_tmp:
                    ref_ray = rays_tmp[len(rays_tmp) // 2]
                    hits = trace_hits(ref_ray, scene, max_hits=1)
                    if len(hits) == 1:
                        d1_px = (hits[0] - ref_ray.pos).length()
                        if d1_px > 1e-9:
                            interaction.um_per_px = interaction.ref_d1_um / d1_px

        if e.type == pygame.MOUSEWHEEL:
            # Selected-only bulge adjustment for LensedMirror
            sel = interaction.selected
            if isinstance(sel, LensedMirror):
                delta = e.y * BULGE_WHEEL_STEP
                sel.adjust_bulge(delta, max_abs=BULGE_WHEEL_MAX_ABS)

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                # Check if exit button clicked
                exit_btn_rect = pygame.Rect(WIDTH - 50, 15, 35, 35)
                if exit_btn_rect.collidepoint((mx, my)):
                    running = False
                    continue
            if not canvas_area.collidepoint((mx, my)):
                continue

            if e.button == 3:
                # Right-click delete
                for obj in list(scene.objects):
                    if hasattr(obj, "contains_point") and obj.contains_point(mouse):
                        if interaction.selected is obj:
                            interaction.selected = None
                        scene.remove(obj)
                        break

            elif e.button == 1:
                # Add-mode: start preview
                if interaction.add_mode:
                    interaction.start_pos = mouse
                    interaction.current_pos = mouse
                    continue

                interaction.dragging = None
                interaction.drag_mode = None
                interaction.last_mouse = mouse

                # Selection + editing
                clicked_obj = None
                for obj in reversed(scene.objects):
                    if not hasattr(obj, "p1") or not hasattr(obj, "p2"):
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
                interaction.current_pos = mouse

            if interaction.dragging and interaction.last_mouse:
                obj = interaction.dragging

                if interaction.drag_mode == "move":
                    dx = mouse.x - interaction.last_mouse.x
                    dy = mouse.y - interaction.last_mouse.y
                    obj.move(dx, dy)

                elif interaction.drag_mode == "p1":
                    obj.p1 = mouse

                elif interaction.drag_mode == "p2":
                    obj.p2 = mouse

                elif interaction.drag_mode == "rotate":
                    cx = (obj.p1.x + obj.p2.x) / 2
                    cy = (obj.p1.y + obj.p2.y) / 2
                    half_len = (obj.p2 - obj.p1).length() / 2
                    angle = math.atan2(my - cy, mx - cx)
                    obj.p1 = Vector(cx - math.cos(angle) * half_len,
                                    cy - math.sin(angle) * half_len)
                    obj.p2 = Vector(cx + math.cos(angle) * half_len,
                                    cy + math.sin(angle) * half_len)

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
                        scene.add(MediaInterface(Vector(a.x, a.y), Vector(b.x, b.y)))
                    elif interaction.add_mode == "beam":
                        scene.add(Beam(Vector(a.x, a.y), Vector(b.x, b.y),
                                       spread_deg=BEAM_DEFAULT_SPREAD_DEG,
                                       pos_spacing_px=BEAM_DEFAULT_POS_SPACING_PX,
                                       angle_samples=BEAM_DEFAULT_ANGLE_SAMPLES,
                                       total_power=1.0))
                elif interaction.add_mode == "fiber": 
                    fiber = FiberSource(a.x, a.y)
                    scene.add(fiber)
                    scene.add(fiber.facet)
                        

                interaction.start_pos = None
                interaction.current_pos = None
                interaction.add_mode = None

            interaction.dragging = None
            interaction.drag_mode = None
            interaction.last_mouse = None

        # --- draw ---
    screen.fill(BG)

    # Modern top bar with gradient feel
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, UI_BAR_H))
    
    # Subtle separator line
    pygame.draw.line(screen, SIDEBAR_BORDER, (0, UI_BAR_H - 1), (WIDTH, UI_BAR_H - 1), 2)
    
    # Title section 
        # Title section 
    title_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 30, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 16)
    
    title = title_font.render("Optical Ray Tracer", True, UI_TEXT_PRIMARY)
    subtitle = subtitle_font.render("Professional Simulation Environment", True, (168, 85, 247))
    
    screen.blit(title, (28, 14))
    screen.blit(subtitle, (29, 55))
    
    # Keyboard hints 
        # Keyboard hints 
    hints_font = pygame.font.SysFont("Segoe UI, Helvetica Neue, Roboto", 17)
    hint_text = "Drag to move  •  SHIFT+drag to rotate  •  Right-click to delete  •  C to calibrate  •  Wheel to adjust bulge"
    hint_surf = hints_font.render(hint_text, True, (170, 180, 200))
    hint_rect = hint_surf.get_rect(topleft=(SIDEBAR_W + 20, 55))
    screen.blit(hint_surf, hint_rect)
    
    # Exit button (top-right)
    exit_btn_rect = pygame.Rect(WIDTH - 50, 15, 35, 35)
    exit_hover = exit_btn_rect.collidepoint((mx, my))
    
    if exit_hover:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    
    # Button background
    exit_color = (168, 85, 247) if exit_hover else (100, 110, 130)
    pygame.draw.rect(screen, exit_color, exit_btn_rect, border_radius=8)
    pygame.draw.rect(screen, (150, 160, 180), exit_btn_rect, 2, border_radius=8)
    
    # X icon 
    line_width = 2
    x_offset = 9
    y_offset = 9
    pygame.draw.line(screen, (240, 240, 240),
                     (exit_btn_rect.x + x_offset, exit_btn_rect.y + y_offset),
                     (exit_btn_rect.x + 35 - x_offset, exit_btn_rect.y + 35 - y_offset), line_width)
    pygame.draw.line(screen, (240, 240, 240),
                     (exit_btn_rect.x + 35 - x_offset, exit_btn_rect.y + y_offset),
                     (exit_btn_rect.x + x_offset, exit_btn_rect.y + 35 - y_offset), line_width)
    
    # Store for click detection
    interaction.exit_btn_rect = exit_btn_rect

    # Sidebar 
    pygame.draw.rect(screen, SIDEBAR_BG, sidebar_area)
    pygame.draw.line(screen, SIDEBAR_BORDER, (SIDEBAR_W, UI_BAR_H), (SIDEBAR_W, HEIGHT), 2)

    # Draw sidebar groups
    screen.set_clip(sidebar_area)
    for g in groups:
        g.draw(screen, font)
    screen.set_clip(None)

    screen.set_clip(None)

    # Reset cursor to default if not hovering any interactive element
    cursor_is_hovering = False
    
    # Check if hovering any button or group header
    for g in groups:
        if g.hovered or any(b.hovered for b in g.buttons):
            cursor_is_hovering = True
            break
    
    # Check if hovering exit button
    if exit_hover:
        cursor_is_hovering = True
    
    # Set cursor based on hover state
    if cursor_is_hovering:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    # Canvas
    screen.set_clip(canvas_area)
    draw_grid(screen)

    # Reset detectors each frame (we redraw & retrace every frame)
    for o in scene.objects:
        if isinstance(o, Detector):
            o.reset()

    # Emit rays
    rays = _emit_rays()
    p_emitted = sum(getattr(r, "power", 1.0) for r in rays)

    trace_rays(rays, scene, screen, um_per_px=interaction.um_per_px)

    # Draw objects
    for o in scene.objects:
        if hasattr(o, 'draw'):
            o.draw(screen)

        # Labels near detectors (with background for visibility)
    for o in scene.objects:
        if isinstance(o, Detector):
            cx = (o.p1.x + o.p2.x) / 2
            cy = (o.p1.y + o.p2.y) / 2
            label = font_small.render(f"{o.count} rays", True, (20, 20, 30))  # Dark text
            
            # Draw background rectangle
            label_rect = label.get_rect(topleft=(cx + 6, cy + 6))
            label_rect.inflate_ip(8, 4)  # Add padding
            pygame.draw.rect(screen, (200, 200, 220), label_rect, border_radius=4)  # Light background
            pygame.draw.rect(screen, (150, 150, 170), label_rect, 1, border_radius=4)  # Border
            
            screen.blit(label, (cx + 6, cy + 6))

    # Preview while adding
    if interaction.add_mode and interaction.start_pos and interaction.current_pos:
        preview_color = (125, 211, 252)
        if interaction.add_mode == "lens":
            preview_color = (134, 239, 172)
        elif interaction.add_mode == "detector":
            preview_color = (248, 113, 113)
        elif interaction.add_mode == "beam":
            preview_color = (167, 139, 250)

        pygame.draw.line(screen, preview_color, interaction.start_pos.tuple(), interaction.current_pos.tuple(), 2)

    screen.set_clip(None)

    # Check for hover on objects for parameter display
    hover_info = None
    for o in scene.objects:
        if hasattr(o, "contains_point") and o.contains_point(mouse):
            if hasattr(o, "get_params_str"):
                hover_info = o.get_params_str()
                break  # Show only the first hovered object

    # Draw hover tooltip box if hovering
    if hover_info:
        tooltip_font = font_small
        line_surfaces = [tooltip_font.render(line, True, (255, 255, 255)) for line in hover_info]
        line_heights = [surf.get_height() for surf in line_surfaces]
        max_width = max(surf.get_width() for surf in line_surfaces)
        total_height = sum(line_heights)
        box_width = max_width + 16  # Padding
        box_height = total_height + 8  # Padding
        tooltip_rect = pygame.Rect(mx + 10, my + 10, box_width, box_height)
        pygame.draw.rect(screen, (100, 100, 100), tooltip_rect, border_radius=4)  # Grey background
        pygame.draw.rect(screen, (150, 150, 150), tooltip_rect, 1, border_radius=4)  # Border
        y_offset = my + 14
        for surf in line_surfaces:
            screen.blit(surf, (mx + 18, y_offset))
            y_offset += surf.get_height()

    # --- Left overlay (units + medium + selection + detectors + IL) ---
    overlay_lines = [
        f"UM_PER_PX = {interaction.um_per_px:.6f} µm/px (press C to calibrate using {interaction.ref_d1_um:.0f} µm)",
        f"Medium alpha = {scene.medium.alpha_per_um:.6g} 1/µm",
        f"Rays emitted = {len(rays)}  |  P_emitted = {p_emitted:.4f}",
    ]

    # Selected element parameters
    sel = interaction.selected
    if isinstance(sel, LensedMirror):
        overlay_lines.append(f"Selected: LensedMirror  bulge={sel.bulge:.2f}px  radius={sel.radius if sel.radius else 0:.2f}px")
    elif isinstance(sel, Lens):
        overlay_lines.append(f"Selected: Lens  f={sel.f:.2f}px")
    elif isinstance(sel, Beam):
        overlay_lines.append(f"Selected: Beam  spread=±{sel.spread_deg:.1f}°  angles={sel.angle_samples}  spacing={sel.pos_spacing_px:.1f}px")
    elif isinstance(sel, Detector):
        overlay_lines.append("Selected: Detector")
    elif isinstance(sel, Mirror):
        overlay_lines.append("Selected: Mirror")

    # Detector stats + IL
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

    # Distance overlay (reference ray)
    if rays and any(isinstance(o, (Mirror, LensedMirror, Lens, Detector)) for o in scene.objects):
        ref_ray = rays[len(rays) // 2]
        hits = trace_hits(ref_ray, scene, max_hits=OVERLAY_MAX_HITS)
        if not hits:
            overlay_lines.append("No element hit from reference ray.")
        else:
            pts = [ref_ray.pos] + hits
            total_um = 0.0
            for i in range(1, len(pts)):
                seg_px = (pts[i] - pts[i - 1]).length()
                seg_um = seg_px * interaction.um_per_px
                total_um += seg_um
                if i == 1:
                    overlay_lines.append(f"d{i} (source→hit{i}) = {seg_um:.2f} µm")
                else:
                    overlay_lines.append(f"d{i} (hit{i-1}→hit{i}) = {seg_um:.2f} µm")
            overlay_lines.append(f"Total (source→hit{len(hits)}) = {total_um:.2f} µm")

    # Overlay lives in the canvas (to the right of the sidebar)
    draw_overlay_lines(screen, font, overlay_lines, x=SIDEBAR_W + 14, y=UI_BAR_H + 10)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
