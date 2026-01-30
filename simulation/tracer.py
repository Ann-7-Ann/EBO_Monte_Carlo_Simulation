import pygame
import math

from config import RAY_COLOR, RAY_WIDTH, MAX_BOUNCES, EPS
from core.ray import Ray
from core.optics import refract_or_reflect


def trace(ray, scene, screen, um_per_px: float = 1.0, draw: bool = True):
    pos = ray.pos
    direction = ray.dir
    power = getattr(ray, "power", 1.0)
    # 2.5D out-of-plane state (pixels)
    u = getattr(ray, "u", 0.0)
    du = getattr(ray, "du", 0.0)

    # Determine current medium slightly ahead of start
    curr_medium = scene.medium_at(pos + direction * 0.5)

    for _ in range(MAX_BOUNCES):
        temp_ray = Ray(
            pos,
            direction,
            ray_id=getattr(ray, "ray_id", None),
            power=power,
            u=u,
            du=du,
        )

        # Nearest optical element hit
        obj, hit = scene.nearest_hit(temp_ray)
        t_obj = (hit - pos).length() if hit is not None else None

        # Nearest medium boundary hit
        bhit, bnorm, m1, m2 = scene.nearest_medium_boundary_hit(temp_ray)
        t_b = (bhit - pos).length() if bhit is not None else None

        # Choose the nearest event
        event = None
        if t_obj is None and t_b is None:
            event = None
        elif t_obj is None:
            event = ("boundary", bhit, bnorm, m1, m2)
        elif t_b is None:
            event = ("element", hit, obj, None, None)
        else:
            if t_b < t_obj:
                event = ("boundary", bhit, bnorm, m1, m2)
            else:
                event = ("element", hit, obj, None, None)

        if event is None:
            end = pos + direction * 2000
            if draw and screen is not None:
                pygame.draw.line(screen, RAY_COLOR, pos.tuple(), end.tuple(), RAY_WIDTH)
            break

        kind = event[0]
        if kind == "boundary":
            hit_pt, normal, m_before, m_after = event[1], event[2], event[3], event[4]
            seg_px = (hit_pt - pos).length()
            seg_um = seg_px * float(um_per_px)
            power = curr_medium.apply_absorption(power, seg_um)
            # Free-space propagation for the out-of-plane coordinate (pixels)
            u = u + du * float(seg_px)

            if draw and screen is not None:
                pygame.draw.line(screen, RAY_COLOR, pos.tuple(), hit_pt.tuple(), RAY_WIDTH)

            new_dir, did_reflect = refract_or_reflect(direction, normal, m_before.n, m_after.n)
            # Tangential component in the out-of-plane axis refracts similarly (paraxial).
            if not did_reflect:
                n1 = float(m_before.n)
                n2 = float(m_after.n)
                if abs(n2) > 1e-12:
                    du = du * (n1 / n2)
            direction = new_dir
            pos = hit_pt + direction * EPS
            curr_medium = scene.medium_at(pos + direction * 0.5)
            continue

        # Optical element hit
        hit_pt, obj = event[1], event[2]
        seg_px = (hit_pt - pos).length()
        seg_um = seg_px * float(um_per_px)
        power = curr_medium.apply_absorption(power, seg_um)
        u = u + du * float(seg_px)
        temp_ray.power = power
        temp_ray.u = u
        temp_ray.du = du

        if draw and screen is not None:
            pygame.draw.line(screen, RAY_COLOR, pos.tuple(), hit_pt.tuple(), RAY_WIDTH)

        direction = obj.interact(temp_ray, hit_pt)
        # Elements may update the out-of-plane slope (e.g., Lens). Persist it.
        u = getattr(temp_ray, "u", u)
        du = getattr(temp_ray, "du", du)
        pos = hit_pt + direction * EPS
        curr_medium = scene.medium_at(pos + direction * 0.5)


def trace_hits(ray, scene, max_hits=30):
    """Return hit points along the ray path, up to max_hits.

    Used for overlays/calibration. This follows only optical elements (not medium boundaries).
    """
    pos = ray.pos
    direction = ray.dir
    u = getattr(ray, "u", 0.0)
    du = getattr(ray, "du", 0.0)
    hits = []

    for _ in range(MAX_BOUNCES):
        temp_ray = Ray(pos, direction, ray_id=None, power=getattr(ray, "power", 1.0), u=u, du=du)
        obj, hit = scene.nearest_hit(temp_ray)
        if not obj:
            break

        hits.append(hit)
        if len(hits) >= max_hits:
            break

        seg_px = (hit - pos).length()
        u = u + du * float(seg_px)
        temp_ray.u = u
        temp_ray.du = du
        direction = obj.interact(temp_ray, hit)
        u = getattr(temp_ray, "u", u)
        du = getattr(temp_ray, "du", du)
        pos = hit + direction * EPS

    return hits


def trace_reference_events(ray, scene, um_per_px: float = 1.0, max_events: int = 12):
    """Trace a single ray and return a compact list of events (boundaries + elements).

    Each returned event is a dict with keys:
      - type: 'boundary' or 'element'
      - pos: hit point (Vector)
      - dir_in / dir_out: incident and outgoing directions (Vector)
      - power: power after traveling to the event (float)
      - For boundary: n1, n2, did_reflect
      - For element: name (class name)

    This follows the same event ordering as `trace()` (nearest of element/boundary),
    but does not draw.
    """
    pos = ray.pos
    direction = ray.dir
    power = getattr(ray, "power", 1.0)
    u = getattr(ray, "u", 0.0)
    du = getattr(ray, "du", 0.0)

    # Determine current medium slightly ahead of start
    curr_medium = scene.medium_at(pos + direction * 0.5)

    events = []

    for _ in range(max(0, int(max_events))):
        temp_ray = Ray(
            pos,
            direction,
            ray_id=getattr(ray, "ray_id", None),
            power=power,
            u=u,
            du=du,
        )

        # Nearest optical element hit
        obj, hit = scene.nearest_hit(temp_ray)
        t_obj = (hit - pos).length() if hit is not None else None

        # Nearest medium boundary hit
        bhit, bnorm, m1, m2 = scene.nearest_medium_boundary_hit(temp_ray)
        t_b = (bhit - pos).length() if bhit is not None else None

        # Choose the nearest event
        if t_obj is None and t_b is None:
            break
        if t_obj is None:
            kind = "boundary"
        elif t_b is None:
            kind = "element"
        else:
            kind = "boundary" if t_b < t_obj else "element"

        if kind == "boundary":
            hit_pt = bhit
            normal = bnorm
            m_before, m_after = m1, m2
            seg_px = (hit_pt - pos).length()
            seg_um = seg_px * float(um_per_px)
            power = curr_medium.apply_absorption(power, seg_um)
            u = u + du * float(seg_px)

            new_dir, did_reflect = refract_or_reflect(direction, normal, m_before.n, m_after.n)
            if not did_reflect:
                n1 = float(m_before.n)
                n2 = float(m_after.n)
                if abs(n2) > 1e-12:
                    du = du * (n1 / n2)

            events.append(
                {
                    "type": "boundary",
                    "pos": hit_pt,
                    "dir_in": direction,
                    "dir_out": new_dir,
                    "power": power,
                    "n1": float(m_before.n),
                    "m1": getattr(m_before, "name", ""),
                    "n2": float(m_after.n),
                    "m2": getattr(m_after, "name", ""),
                    "did_reflect": bool(did_reflect),
                }
            )

            direction = new_dir
            pos = hit_pt + direction * EPS
            curr_medium = scene.medium_at(pos + direction * 0.5)
            continue

        # Optical element hit
        hit_pt = hit
        seg_px = (hit_pt - pos).length()
        seg_um = seg_px * float(um_per_px)
        power = curr_medium.apply_absorption(power, seg_um)
        u = u + du * float(seg_px)
        temp_ray.power = power
        temp_ray.u = u
        temp_ray.du = du

        new_dir = obj.interact(temp_ray, hit_pt)
        u = getattr(temp_ray, "u", u)
        du = getattr(temp_ray, "du", du)
        events.append(
            {
                "type": "element",
                "pos": hit_pt,
                "dir_in": direction,
                "dir_out": new_dir,
                "power": power,
                "name": type(obj).__name__,
            }
        )

        direction = new_dir
        pos = hit_pt + direction * EPS
        curr_medium = scene.medium_at(pos + direction * 0.5)

    return events


def trace_rays(
    rays,
    scene,
    screen,
    um_per_px: float = 1.0,
    draw: bool = True,
    draw_cap: int | None = None,
):
    """Trace all rays for physics/detectors, but optionally draw only a subset.

    Drawing thousands of rays can freeze the UI. When draw=True, we draw at most
    draw_cap rays by evenly sub-sampling the list, while still tracing every ray.
    """

    # If drawing is disabled (or no screen), trace all rays without rendering.
    if (not draw) or (screen is None):
        for ray in rays:
            trace(ray, scene, None, um_per_px=um_per_px, draw=False)
        return

    n = len(rays)
    if draw_cap is None or draw_cap <= 0:
        stride = 1
    else:
        stride = max(1, int(math.ceil(n / float(draw_cap))))

    for i, ray in enumerate(rays):
        # Draw every Nth ray; trace all rays.
        if (i % stride) == 0:
            trace(ray, scene, screen, um_per_px=um_per_px, draw=True)
        else:
            trace(ray, scene, None, um_per_px=um_per_px, draw=False)