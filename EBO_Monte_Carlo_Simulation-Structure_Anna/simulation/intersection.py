from core.vector import Vector

def ray_segment(ray, p1, p2):
    r = ray.dir
    s = p2 - p1
    qp = p1 - ray.pos

    denom = r.x * s.y - r.y * s.x
    if abs(denom) < 1e-6:
        return None

    t = (qp.x * s.y - qp.y * s.x) / denom
    u = (qp.x * r.y - qp.y * r.x) / denom

    if t > 0 and 0 <= u <= 1:
        return ray.pos + r * t
    return None


def ray_segment_t(ray, p1, p2):
    """Ray/segment intersection with parametric distance.

    Returns (t, u, hit_point) where:
        hit = ray.pos + ray.dir * t
        hit = p1 + (p2-p1) * u
    Only valid when t > 0 and 0 <= u <= 1.
    """
    r = ray.dir
    s = p2 - p1
    qp = p1 - ray.pos

    denom = r.x * s.y - r.y * s.x
    if abs(denom) < 1e-6:
        return None

    t = (qp.x * s.y - qp.y * s.x) / denom
    u = (qp.x * r.y - qp.y * r.x) / denom

    if t > 0 and 0 <= u <= 1:
        return t, u, ray.pos + r * t
    return None
