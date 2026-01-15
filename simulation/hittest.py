import math

def point_segment_distance(p, a, b):
    # p = point, a,b = segment endpoints
    ax, ay = a.x, a.y
    bx, by = b.x, b.y
    px, py = p.x, p.y

    dx = bx - ax
    dy = by - ay

    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * dx + (py - ay) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))

    cx = ax + t * dx
    cy = ay + t * dy

    return math.hypot(px - cx, py - cy)
