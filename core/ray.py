import math
from core.vector import Vector

class Ray:
    def __init__(self, pos, direction):
        self.pos = pos
        self.dir = direction.normalize()

    @classmethod
    def from_angle(cls, x, y, angle_deg):
        angle_rad = math.radians(angle_deg)
        direction = Vector(
            math.cos(angle_rad),
            math.sin(angle_rad)
        )
        return cls(Vector(x, y), direction)

