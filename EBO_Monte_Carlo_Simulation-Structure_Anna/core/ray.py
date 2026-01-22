import math
from core.vector import Vector


class Ray:
    """A 2D ray.

    - `ray_id` is used to count unique rays in detectors.
    - `power` is used to compute insertion loss (IL).
    """

    def __init__(
        self,
        pos: Vector,
        direction: Vector,
        ray_id: int | None = None,
        power: float = 1.0,
    ):
        self.pos = pos
        self.dir = direction.normalize()
        self.ray_id = ray_id
        self.power = float(power)

    @classmethod
    def from_angle(cls, x: float, y: float, angle_deg: float, **kwargs):
        angle_rad = math.radians(angle_deg)
        direction = Vector(math.cos(angle_rad), math.sin(angle_rad))
        return cls(Vector(x, y), direction, **kwargs)
