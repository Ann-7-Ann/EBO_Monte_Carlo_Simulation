import math
import pygame

from components.element import OpticalElement
from core.vector import Vector
from config import LENSED_MIRROR_COLOR
from simulation.hittest import point_segment_distance


def _norm_angle(a: float) -> float:
    """Normalize angle to [0, 2π)."""
    a = a % (2 * math.pi)
    return a if a >= 0 else a + 2 * math.pi


def _angle_in_ccw_interval(a: float, start: float, end: float) -> bool:
    """Return True if angle a lies on the CCW interval start->end."""
    a = _norm_angle(a)
    start = _norm_angle(start)
    end = _norm_angle(end)
    if start <= end:
        return start <= a <= end
    return a >= start or a <= end


class LensedMirror(OpticalElement):
    """A circular-arc ("lensed") mirror defined by two endpoints + sagitta (bulge).

    - p1, p2: chord endpoints
    - bulge: signed sagitta in pixels (distance from chord midpoint to arc along chord normal)

    Convention:
    - Positive bulge curves towards +perp(chord) (using chord.perp()).
    - Negative bulge curves the opposite way.
    """

    def __init__(self, p1: Vector, p2: Vector, bulge: float = 40.0):
        self.p1 = p1
        self.p2 = p2
        self.bulge = float(bulge)

        # cached arc geometry
        self._center: Vector | None = None
        self._radius: float | None = None
        self._arc_start: float | None = None
        self._arc_end: float | None = None
        self._update_geometry()

    # ---- public helpers ----
    def set_bulge(self, bulge: float):
        """Set bulge (signed), allowing negative values."""
        self.bulge = float(bulge)
        # Allow exactly 0 (degenerates to a straight segment fallback)
        if abs(self.bulge) < 1e-6:
            self.bulge = 0.0
        self._update_geometry()

    def adjust_bulge(self, delta: float, max_abs: float | None = None):
        """Add delta to bulge, with optional maximum absolute clamp."""
        b = self.bulge + float(delta)
        if max_abs is not None:
            b = max(-abs(max_abs), min(abs(max_abs), b))
        self.set_bulge(b)

    # ---- geometry ----
    def _update_geometry(self):
        chord = self.p2 - self.p1
        L = chord.length()
        if L < 1e-6 or abs(self.bulge) < 1e-6:
            self._center = None
            self._radius = None
            self._arc_start = None
            self._arc_end = None
            return

        m = Vector((self.p1.x + self.p2.x) / 2.0, (self.p1.y + self.p2.y) / 2.0)
        n = chord.perp().normalize()  # chord normal
        s = self.bulge

        # Circle radius from chord length L and sagitta s:
        # R = (L^2)/(8s) + s/2
        R = (L * L) / (8.0 * s) + s / 2.0
        R_abs = abs(R)

        # Center lies along the chord normal from the midpoint:
        # distance from midpoint to center: h = R - s
        h = R - s
        center = m + n * h

        # Define which arc we mean using a mid-arc point.
        mid_arc = m + n * s

        a1 = math.atan2(self.p1.y - center.y, self.p1.x - center.x)
        a2 = math.atan2(self.p2.y - center.y, self.p2.x - center.x)
        am = math.atan2(mid_arc.y - center.y, mid_arc.x - center.x)

        # Choose the CCW interval that contains the mid-arc point.
        if _angle_in_ccw_interval(am, a1, a2):
            arc_start, arc_end = a1, a2
        else:
            arc_start, arc_end = a2, a1

        self._center = center
        self._radius = R_abs
        self._arc_start = arc_start
        self._arc_end = arc_end

    @property
    def center(self):
        self._update_geometry()
        return self._center

    @property
    def radius(self):
        self._update_geometry()
        return self._radius

    # ---- ray optics ----
    def intersect(self, ray):
        """Return closest hit point on the arc, or None."""
        self._update_geometry()
        if self._center is None or self._radius is None:
            # degenerate: treat as a flat segment (fallback)
            from simulation.intersection import ray_segment
            return ray_segment(ray, self.p1, self.p2)

        o = ray.pos
        d = ray.dir
        c = self._center
        R = self._radius

        # Solve |o + t d - c|^2 = R^2
        fx = o.x - c.x
        fy = o.y - c.y
        a = d.x * d.x + d.y * d.y
        b = 2.0 * (fx * d.x + fy * d.y)
        cc = fx * fx + fy * fy - R * R

        disc = b * b - 4.0 * a * cc
        if disc < 0:
            return None

        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2.0 * a)
        t2 = (-b + sqrt_disc) / (2.0 * a)

        candidates = []
        for t in (t1, t2):
            if t <= 1e-9:
                continue
            p = Vector(o.x + d.x * t, o.y + d.y * t)
            ang = math.atan2(p.y - c.y, p.x - c.x)
            if _angle_in_ccw_interval(ang, self._arc_start, self._arc_end):
                candidates.append((t, p))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def interact(self, ray, hit):
        """Specular reflection using the local surface normal at the hit point."""
        self._update_geometry()
        if self._center is None:
            # fallback flat behavior
            chord_n = (self.p2 - self.p1).perp().normalize()
            v = ray.dir
            return v - chord_n * 2 * v.dot(chord_n)

        n = (hit - self._center).normalize()
        v = ray.dir
        return v - n * 2 * v.dot(n)

    # ---- drawing / hit testing ----
    def _sample_points(self, n=40):
        """Sample points along the arc for drawing."""
        self._update_geometry()
        if self._center is None or self._radius is None:
            return [self.p1, self.p2]

        start = _norm_angle(self._arc_start)
        end = _norm_angle(self._arc_end)
        # unwrap end so that we go CCW from start to end
        if end < start:
            end += 2 * math.pi

        pts = []
        for i in range(n + 1):
            t = i / n
            ang = start + (end - start) * t
            pts.append(
                Vector(
                    self._center.x + math.cos(ang) * self._radius,
                    self._center.y + math.sin(ang) * self._radius,
                )
            )
        return pts

    def draw(self, screen):
        pts = self._sample_points(50)
        if len(pts) >= 2:
            pygame.draw.lines(screen, LENSED_MIRROR_COLOR, False, [p.tuple() for p in pts], 3)

    def contains_point(self, pos: Vector):
        """Hit-test the arc (approx)."""
        self._update_geometry()
        if self._center is None or self._radius is None:
            return point_segment_distance(pos, self.p1, self.p2) < 8

        # Check radial distance close to R and angle within arc.
        dx = pos.x - self._center.x
        dy = pos.y - self._center.y
        r = math.hypot(dx, dy)
        if abs(r - self._radius) > 8:
            return False
        ang = math.atan2(dy, dx)
        return _angle_in_ccw_interval(ang, self._arc_start, self._arc_end)
