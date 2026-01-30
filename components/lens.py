import pygame

from components.element import OpticalElement
from core.matrices import thin_lens
from core.transform import ray_to_theta, theta_to_dir
from config import LENS_COLOR
from simulation.hittest import point_segment_distance


class Lens(OpticalElement):
    """Thin lens represented as a segment.

    The lens segment is the aperture line. The optical axis is perpendicular to
    the segment (through its midpoint).

    State vector used for ABCD:
      [y, theta] where:
        y     = transverse position along the segment relative to its midpoint
        theta = paraxial slope (transverse / axial) relative to the optical axis
    """

    def __init__(self, p1, p2, f):
        self.p1 = p1
        self.p2 = p2
        self.f = float(f)

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        direction = ray.dir

        tangent = (self.p2 - self.p1).normalize()          # along segment (transverse)
        axis = tangent.perp().normalize()                  # optical axis (normal to segment)
        center = (self.p1 + self.p2) * 0.5

        # Height along the lens aperture
        y = (hit - center).dot(tangent)

        # Paraxial slope relative to optical axis
        theta = ray_to_theta(direction, axis, tangent)

        M = thin_lens(self.f)
        y2, theta2 = (M @ [[y], [theta]]).flatten()
        _ = y2  # y2 is not needed for direction update at the lens plane

        # --- 2.5D out-of-plane focusing ---
        # If the ray carries an out-of-plane coordinate `u` (pixels) and slope
        # `du` (dimensionless), apply the same thin-lens update in that axis:
        #   du_out = du_in - u/f
        # This assumes the lens is spherical (same focal length in both axes).
        try:
            f = float(self.f)
            if abs(f) > 1e-12 and hasattr(ray, "u") and hasattr(ray, "du"):
                ray.du = float(ray.du) - float(ray.u) / f
        except Exception:
            pass

        return theta_to_dir(theta2, axis, tangent)

    def draw(self, screen):
        pygame.draw.line(screen, LENS_COLOR, self.p1.tuple(), self.p2.tuple(), 2)

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8

    def get_params_str(self):
        return [
            f"Lens: p1=({self.p1.x:.1f}, {self.p1.y:.1f})",
            f"p2=({self.p2.x:.1f}, {self.p2.y:.1f}), f={self.f:.2f}px"
        ]
