import pygame

from config import RAY_COLOR, RAY_WIDTH, MAX_BOUNCES, EPS
from core.ray import Ray


def trace(ray, scene, screen, um_per_px: float = 1.0):
    pos = ray.pos
    direction = ray.dir
    power = getattr(ray, "power", 1.0)

    for _ in range(MAX_BOUNCES):
        obj, hit = scene.nearest_hit(Ray(pos, direction, ray_id=ray.ray_id, power=power))
        if not obj:
            end = pos + direction * 2000
            pygame.draw.line(screen, RAY_COLOR, pos.tuple(), end.tuple(), RAY_WIDTH)
            break

        # Travel distance to hit
        seg_um = (hit - pos).length() * um_per_px
        power = scene.medium.apply_absorption(power, seg_um)

        pygame.draw.line(screen, RAY_COLOR, pos.tuple(), hit.tuple(), RAY_WIDTH)

        # Interaction gives new direction (TIR/refraction)
        direction = obj.interact(Ray(pos, direction, power=power), hit)

        # Step slightly forward
        pos = hit + direction * EPS



def trace_hits(ray, scene, max_hits=30):
    """Return hit points along the ray path, up to max_hits.

    This is used for overlays/calibration; it avoids side-effects in detectors by
    passing ray_id=None.
    """
    pos = ray.pos
    direction = ray.dir
    hits = []

    for _ in range(MAX_BOUNCES):
        temp_ray = Ray(pos, direction, ray_id=None, power=getattr(ray, "power", 1.0))
        obj, hit = scene.nearest_hit(temp_ray)
        if not obj:
            break

        hits.append(hit)
        if len(hits) >= max_hits:
            break

        direction = obj.interact(temp_ray, hit)
        pos = hit + direction * EPS

    return hits


def trace_rays(rays, scene, screen, um_per_px: float = 1.0):
    for ray in rays:
        trace(ray, scene, screen, um_per_px=um_per_px)
