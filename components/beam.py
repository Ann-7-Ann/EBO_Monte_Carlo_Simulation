import math
import pygame

from core.vector import Vector
from core.ray import Ray
from config import BEAM_COLOR
from simulation.hittest import point_segment_distance


class Beam:
    """A segment-based source that emits rays approximately perpendicular to the segment.

    Parameters control a simple "fan" emission:
      - position samples along the segment (based on spacing)
      - angle samples within [-spread_deg, +spread_deg] around the normal direction

    This class is *not* an OpticalElement (it doesn't interact with rays).
    """

    def __init__(
        self,
        p1: Vector,
        p2: Vector,
        spread_deg: float = 10.0,
        pos_spacing_px: float = 10.0,
        angle_samples: int = 5,
        total_power: float = 1.0,
    ):
        self.p1 = p1
        self.p2 = p2
        self.spread_deg = float(spread_deg)
        self.pos_spacing_px = float(pos_spacing_px)
        self.angle_samples = int(angle_samples)
        self.total_power = float(total_power)

    def emit(self, ray_id_start=0):
        chord = self.p2 - self.p1
        L = chord.length()
        if L < 1e-6:
            return []

        # direction perpendicular to the beam segment
        tangent = chord.normalize()
        normal = tangent.perp().normalize()  # nominal emission direction

        # samples along segment
        n_pos = max(1, int(L / max(1.0, self.pos_spacing_px)) + 1)

        # angular samples
        n_ang = max(1, self.angle_samples)
        spread_rad = math.radians(self.spread_deg)

        total_rays = n_pos * n_ang
        per_ray_power = self.total_power / total_rays if total_rays > 0 else 0.0

        rays = []
        ray_id = ray_id_start
        for i in range(n_pos):
            t = i / (n_pos - 1) if n_pos > 1 else 0.5
            origin = self.p1 + chord * t

            for j in range(n_ang):
                if n_ang == 1:
                    a = 0.0
                else:
                    u = (j / (n_ang - 1)) * 2.0 - 1.0
                    a = u * spread_rad

                # rotate normal by angle a
                ca = math.cos(a)
                sa = math.sin(a)
                d = Vector(
                    normal.x * ca - normal.y * sa,
                    normal.x * sa + normal.y * ca,
                )

                rays.append(Ray(origin, d, ray_id=ray_id, power=per_ray_power))
                ray_id += 1

        return rays

    def draw(self, screen):
        pygame.draw.line(screen, BEAM_COLOR, self.p1.tuple(), self.p2.tuple(), 4)

    def move(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy

    def contains_point(self, pos: Vector):
        return point_segment_distance(pos, self.p1, self.p2) < 8
