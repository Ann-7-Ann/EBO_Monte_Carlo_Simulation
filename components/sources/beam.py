import math
import random
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

    def emit(self, ray_id_start=0, rng: random.Random | None = None):
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

        # 2.5D emission: sample an out-of-plane coordinate `u` and slope `du`
        # (both in pixels units). This lets detectors reconstruct a 2D
        # cross-section (x=along detector, y=u).
        #
        # We model a simple Gaussian beam at the source:
        #   - in-plane transverse coordinate is along the segment (y)
        #   - out-of-plane coordinate u is sampled from a matching Gaussian
        #   - out-of-plane angle is sampled with sigma ~ spread/3
        if rng is None:
            rng = None

        sigma_y = max(1e-6, L / 6.0)  # so +/-3sigma covers most of the segment
        sigma_u = sigma_y
        sigma_theta_u = spread_rad / 3.0 if spread_rad > 1e-12 else 0.0

        rays = []
        weights = []
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

                # In-plane transverse coordinate (along segment)
                center = (self.p1 + self.p2) * 0.5
                y = (origin - center).dot(tangent)
                w_y = math.exp(-0.5 * (y / sigma_y) ** 2) if sigma_y > 0 else 1.0

                if rng is not None:
                    u = rng.gauss(0.0, sigma_u)
                    theta_u = rng.gauss(0.0, sigma_theta_u)
                    du = math.tan(theta_u)
                    w_u = math.exp(-0.5 * (u / sigma_u) ** 2) if sigma_u > 0 else 1.0
                else:
                    u = 0.0
                    du = 0.0
                    w_u = 1.0

                rays.append(Ray(origin, d, ray_id=ray_id, power=0.0, u=u, du=du))
                weights.append(w_y * w_u)
                ray_id += 1

        # Normalize gaussian weights to total_power
        sw = float(sum(weights)) if weights else 0.0
        if sw > 0:
            for r, w in zip(rays, weights):
                r.power = self.total_power * (float(w) / sw)
        else:
            # Fallback: uniform
            total_rays = len(rays)
            per = self.total_power / total_rays if total_rays > 0 else 0.0
            for r in rays:
                r.power = per

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

    def get_params_str(self):
        return [
            f"Beam: p1=({self.p1.x:.1f}, {self.p1.y:.1f}), p2=({self.p2.x:.1f}, {self.p2.y:.1f})",
            f"spread={self.spread_deg:.1f}°, angles={self.angle_samples}",
            f"spacing={self.pos_spacing_px:.1f}px, power={self.total_power:.4f}"
        ]
