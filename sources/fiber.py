import math
import pygame
from core.vector import Vector
from core.ray import Ray
from core.transform import deg_to_rad
from config import BEAM_COLOR

class FiberSource:
    def __init__(
        self,
        pos_x,                     # position along propagation axis
        pos_y,
        mfd=9.232917,             # mode field diameter
        cladding_diameter=124.9329,
        n_core=1.4527,
        cleave_angle=8.0,         # degrees
        core_offset=(0, 0),       # (x, y)
        angle_deg=0.0,            # central launch angle
        offset=(0.0, 0.0),        # transverse offset
        total_power=1.0,
    ):
        self.pos = Vector(pos_x, pos_y)
        self.mfd = mfd
        self.cladding_diameter = cladding_diameter
        self.n_core = n_core

        self.cleave_angle = deg_to_rad(cleave_angle)
        self.core_offset = Vector(*core_offset)
        self.angle = deg_to_rad(angle_deg)
        self.offset = Vector(*offset)
        self.total_power = float(total_power)

    def emit(self, num_rays=11, ray_id_start=0):
        """Emit rays with unique IDs and equal per-ray power.

        Returns:
            list[Ray]
        """
        rays = []
        if num_rays <= 0:
            return rays

        waist = self.mfd / 2.0
        per_ray_power = self.total_power / num_rays

        for i in range(num_rays):
            u = (i / (num_rays - 1)) * 2 - 1 if num_rays > 1 else 0.0

            # transverse offset (screen y)
            y = self.pos.y + u * waist + self.offset.y + self.core_offset.y
            x = self.pos.x + self.offset.x + self.core_offset.x

            # simple paraxial launch angle model
            theta = self.angle + self.cleave_angle + u * (waist / self.mfd)
            direction = Vector(math.cos(theta), math.sin(theta))

            rays.append(
                Ray(
                    Vector(x, y),
                    direction,
                    ray_id=ray_id_start + i,
                    power=per_ray_power,
                )
            )

        return rays


    def draw(self, screen):
        pygame.draw.circle(screen, BEAM_COLOR, (self.pos.x, self.pos.y), 5)

    def get_params_str(self):
        return [
            f"Fiber: pos=({self.pos.x:.1f}, {self.pos.y:.1f})",
            f"mfd={self.mfd:.2f}, cladding_d={self.cladding_diameter:.2f}",
            f"n_core={self.n_core:.3f}, cleave_angle={math.degrees(self.cleave_angle):.1f}°",
            f"core_offset=({self.core_offset.x:.2f}, {self.core_offset.y:.2f})",
            f"angle={math.degrees(self.angle):.1f}°, offset=({self.offset.x:.2f}, {self.offset.y:.2f})",
            f"power={self.total_power:.4f}"
        ]

    def contains_point(self, pos: Vector):
        return (pos - self.pos).length() < 10
