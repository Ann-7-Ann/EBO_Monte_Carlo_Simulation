import math
from core.vector import Vector
from core.ray import Ray
from core.transform import deg_to_rad

class FiberSource:
    def __init__(
        self,
        pos_x,                     # position along propagation axis
        pos_y,
        mfd = 9.232917,                   # mode field diameter
        cladding_diameter = 124.9329,
        n_core = 1.4527,
        cleave_angle= 8.0,      # degrees
        core_offset=(0, 0),    # (x, y)
        angle_deg=0.0,          # central launch angle/pedestal
        offset=(0.0, 0.0)       # transverse offset
    ):
        self.pos = Vector(pos_x,pos_y)
        self.mfd = mfd
        self.cladding_diameter = cladding_diameter
        self.n_core = n_core

        self.cleave_angle = deg_to_rad(self,cleave_angle)
        self.core_offset = Vector(*core_offset)
        self.angle = deg_to_rad (self,angle_deg)
        self.offset = Vector(*offset)

    
    def emit(self, num_rays=11):
        rays = []

        waist = self.mfd / 2

        for i in range(num_rays):
            # [-1, 1] across mode field
            u = (i / (num_rays - 1)) * 2 - 1 if num_rays > 1 else 0

            # transverse offset (screen y)
            y = self.pos.y + u * waist + self.offset.y
            x = self.pos.x + self.offset.x

            # paraxial launch angle
            theta = self.angle + self.cleave_angle + u * (waist / self.mfd)

            direction = Vector(
                math.cos(theta),
                math.sin(theta)
            )

            rays.append(Ray(Vector(x, y), direction))

        return rays


    