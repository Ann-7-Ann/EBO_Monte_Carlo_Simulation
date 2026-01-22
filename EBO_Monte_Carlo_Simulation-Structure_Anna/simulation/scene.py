from components.element import OpticalElement
from media.medium import Medium
from core.vector import Vector
from config import EPS


class Scene:
    def __init__(self, medium: Medium | None = None):
        self.objects: list[object] = []
        self.medium: Medium = medium if medium is not None else Medium(n=1.0, alpha_per_um=0.0, name="air")

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def clear_by_type(self, cls):
        """Remove all objects that are instances of cls."""
        self.objects = [o for o in self.objects if not isinstance(o, cls)]

    # --- Optical element hits ---

    def nearest_hit(self, ray):
        """Return (obj, hit_point) for the nearest OpticalElement intersection."""
        best = None
        obj_hit = None
        hit = None

        for o in self.objects:
            if not isinstance(o, OpticalElement):
                continue
            h = o.intersect(ray)
            if h is None:
                continue
            d = (h - ray.pos).length()
            if best is None or d < best:
                best = d
                obj_hit = o
                hit = h

        return (obj_hit, hit) if obj_hit else (None, None)

    # --- Media handling ---

    def media_polygons(self):
        from components.media_polygon import MediaPolygon
        return [o for o in self.objects if isinstance(o, MediaPolygon)]

    def medium_at(self, pos: Vector) -> Medium:
        """Return the medium at a given point.

        If multiple media overlap, the last-added polygon wins.
        """
        m = self.medium
        for poly in self.media_polygons():
            if poly.contains_point(pos):
                m = poly.medium
        return m

    def nearest_medium_boundary_hit(self, ray):
        """Return the nearest hit with any MediaPolygon boundary.

        Returns:
            (hit_point, normal, m_before, m_after) or (None, None, None, None)
        """
        from simulation.intersection import ray_segment_t

        best_t = None
        best_hit = None
        best_normal = None
        best_m1 = None
        best_m2 = None

        # A slightly larger epsilon for classifying sides.
        s = 0.5

        for poly in self.media_polygons():
            pts = poly.points
            if len(pts) < 3:
                continue
            for i in range(len(pts)):
                a = pts[i]
                b = pts[(i + 1) % len(pts)]
                res = ray_segment_t(ray, a, b)
                if res is None:
                    continue
                t, u, hit = res
                if t <= max(1e-6, EPS * 10):
                    continue

                # Determine medium on either side along the ray direction.
                before_pt = hit - ray.dir * s
                after_pt = hit + ray.dir * s
                m_before = self.medium_at(before_pt)
                m_after = self.medium_at(after_pt)
                if m_before is m_after:
                    continue  # not a real boundary crossing

                # Edge normal candidates
                edge = (b - a).normalize()
                n_cand = edge.perp().normalize()

                # Orient normal so that it points from m_before -> m_after
                # by sampling on normal's +/- side.
                m_plus = self.medium_at(hit + n_cand * s)
                m_minus = self.medium_at(hit - n_cand * s)
                if m_plus is m_after and m_minus is m_before:
                    normal = n_cand
                elif m_plus is m_before and m_minus is m_after:
                    normal = n_cand * -1.0
                else:
                    # Fallback: use candidate; refraction routine will flip as needed.
                    normal = n_cand

                if best_t is None or t < best_t:
                    best_t = t
                    best_hit = hit
                    best_normal = normal
                    best_m1 = m_before
                    best_m2 = m_after

        return best_hit, best_normal, best_m1, best_m2