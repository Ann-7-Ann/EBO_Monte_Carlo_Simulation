from components.element import OpticalElement
from media.medium import Medium


class Scene:
    def __init__(self, medium: Medium | None = None):
        self.objects = []
        self.medium = medium if medium is not None else Medium(k=0.0, wavelength_um=1.31)

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def clear_by_type(self, cls):
        """Remove all objects that are instances of cls."""
        self.objects = [o for o in self.objects if not isinstance(o, cls)]

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
