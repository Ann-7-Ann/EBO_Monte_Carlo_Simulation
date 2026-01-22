from core.vector import Vector
from config import GRID_STEP_PX, SNAP_RADIUS_PX


def _snap_to_grid(p: Vector) -> Vector:
    gx = round(p.x / GRID_STEP_PX) * GRID_STEP_PX
    gy = round(p.y / GRID_STEP_PX) * GRID_STEP_PX
    return Vector(gx, gy)


def collect_snap_targets(scene, extra_points=None):
    targets = []
    if extra_points:
        targets.extend(extra_points)

    for o in scene.objects:
        # Segment endpoints
        if hasattr(o, "p1") and hasattr(o, "p2"):
            targets.append(o.p1)
            targets.append(o.p2)
        # Polygon vertices
        if hasattr(o, "points") and isinstance(getattr(o, "points"), list):
            for p in o.points:
                targets.append(p)
    return targets


def snap_point(p: Vector, scene, enabled: bool = True, radius_px: float = SNAP_RADIUS_PX, extra_points=None) -> Vector:
    if not enabled:
        return p

    best = None
    best_d = None

    # Prefer snapping to existing points
    targets = collect_snap_targets(scene, extra_points=extra_points)
    for t in targets:
        d = (p - t).length()
        if d <= radius_px and (best_d is None or d < best_d):
            best = t
            best_d = d

    if best is not None:
        return Vector(best.x, best.y)

    # Otherwise, snap to grid if close
    g = _snap_to_grid(p)
    if (p - g).length() <= radius_px:
        return g

    return p
