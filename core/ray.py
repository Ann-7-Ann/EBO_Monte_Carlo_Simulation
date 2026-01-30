import math
from core.vector import Vector


class Ray:
    """A 2D ray with an optional out-of-plane ("2.5D") state.

    - `ray_id` is used to count unique rays in detectors.
    - `power` is used to compute insertion loss (IL).

    2.5D support
    -----------
    We keep an extra transverse coordinate `u` (in pixels) and a paraxial slope
    `du` (dimensionless, approximately ``tan(theta_u)``). These do *not* affect
    2D intersection tests, but allow detectors to reconstruct a 2D beam
    cross-section (x = along detector segment, y = out-of-plane `u`) and plot
    intensity (z = accumulated power).
    """

    def __init__(
        self,
        pos: Vector,
        direction: Vector,
        ray_id: int | None = None,
        power: float = 1.0,
        u: float = 0.0,
        du: float = 0.0,
    ):
        self.pos = pos
        self.dir = direction.normalize()
        self.ray_id = ray_id
        self.power = float(power)
        # 2.5D out-of-plane state (pixels)
        self.u = float(u)
        self.du = float(du)

    @classmethod
    def from_angle(cls, x: float, y: float, angle_deg: float, **kwargs):
        angle_rad = math.radians(angle_deg)
        direction = Vector(math.cos(angle_rad), math.sin(angle_rad))
        return cls(Vector(x, y), direction, **kwargs)
