class Scene:
    def __init__(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def nearest_hit(self, ray):
        best = None
        obj_hit = None
        for o in self.objects:
            h = o.intersect(ray)
            if h:
                d = (h - ray.pos).length()
                if not best or d < best:
                    best = d
                    obj_hit = o
                    hit = h
        return obj_hit, hit if obj_hit else (None, None)
