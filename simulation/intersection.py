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
