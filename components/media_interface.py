import pygame

from components.element import OpticalElement
from core.optics import refract_or_reflect
from simulation.hittest import point_segment_distance


class MediaInterface(OpticalElement):
    """Straight boundary between two optical media.

    Convention:
        The interface normal points from medium n1 to medium n2.
        (Normal is derived from segment direction using `perp()`; swap endpoints
        if you want to flip the convention.)

    Notes:
        Refraction is computed with Snell's law. We choose the correct
        (n1,n2) ordering depending on which side the incident ray approaches
        from.
    """

    def __init__(self, p1, p2, n1: float = 1.0, n2: float = 1.0):
        self.p1 = p1
        self.p2 = p2
        self.n1 = float(n1)
        self.n2 = float(n2)

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        # Segment tangent and the convention normal from n1->n2.
        axis = (self.p2 - self.p1).normalize()
        normal_12 = axis.perp().normalize()

        i_dir = ray.dir.normalize()

        # Decide which side the ray comes from and pick indices accordingly.
        if i_dir.dot(normal_12) > 0.0:
            # Ray travels from n1 -> n2
            n1, n2 = self.n1, self.n2
            n_incident = normal_12 * -1.0  # oppose incident direction
        else:
            # Ray travels from n2 -> n1
            n1, n2 = self.n2, self.n1
            n_incident = normal_12  # oppose incident direction

        new_dir, did_reflect = refract_or_reflect(i_dir, n_incident, n1, n2)

        # --- 2.5D out-of-plane refraction (paraxial) ---
        # Tangential components refract as sin(theta2) = (n1/n2) sin(theta1).
        # For small angles, slope scales approximately by n1/n2.
        if not did_reflect and hasattr(ray, "du"):
            try:
                if abs(float(n2)) > 1e-12:
                    ray.du = float(ray.du) * (float(n1) / float(n2))
            except Exception:
                pass

        return new_dir

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8

    def draw(self, screen):
        pygame.draw.line(screen, (255, 255, 255), self.p1.tuple(), self.p2.tuple(), 1)

    def get_params_str(self):
        return [
            f"Interface: p1=({self.p1.x:.1f}, {self.p1.y:.1f})",
            f"p2=({self.p2.x:.1f}, {self.p2.y:.1f})",
            f"n1={self.n1:.3f}, n2={self.n2:.3f}",
        ]
