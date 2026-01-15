from core.ray import Ray

class LightSource:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

    def emit(self):
        r = Ray.from_angle(self.x, self.y, self.angle)
        r.ray_id = 0
        return r