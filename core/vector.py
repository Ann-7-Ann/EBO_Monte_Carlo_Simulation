import math

class Vector:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, o): return Vector(self.x + o.x, self.y + o.y)
    def __sub__(self, o): return Vector(self.x - o.x, self.y - o.y)
    def __mul__(self, s): return Vector(self.x * s, self.y * s)

    def dot(self, o): return self.x * o.x + self.y * o.y

    def length(self): return math.hypot(self.x, self.y)

    def normalize(self):
        l = self.length()
        return Vector(self.x / l, self.y / l) if l else Vector(1, 0)

    def perp(self):
        return Vector(-self.y, self.x)

    def tuple(self):
        return int(self.x), int(self.y)
    
    def __neg__(self):
        return Vector(-self.x, -self.y)
