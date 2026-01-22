import pygame

from components.element import OpticalElement
from config import DETECTOR_COLOR
from simulation.hittest import point_segment_distance


class Detector(OpticalElement):
    """A segment detector.

    Behavior:
    - pass-through: does not change direction
    - unique counting: each ray is counted only once per frame (by ray_id)
    - power accumulation: sums power at first intersection (used for IL)
    """

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self._seen_ray_ids: set[int] = set()
        self._power_by_ray_id: dict[int, float] = {}  # ray_id -> power at first hit

    @property
    def count(self) -> int:
        return len(self._seen_ray_ids)

    @property
    def power_sum(self) -> float:
        return float(sum(self._power_by_ray_id.values()))

    @property
    def power_by_ray_id(self) -> dict[int, float]:
        """Mapping ray_id -> power at first detector hit (read-only view)."""
        return dict(self._power_by_ray_id)

    def reset(self):
        """Clear counts for the current frame/simulation run."""
        self._seen_ray_ids.clear()
        self._power_by_ray_id.clear()

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        rid = getattr(ray, "ray_id", None)
        if rid is not None and rid not in self._seen_ray_ids:
            self._seen_ray_ids.add(rid)
            self._power_by_ray_id[rid] = float(getattr(ray, "power", 0.0))
        return ray.dir

    def draw(self, screen):
        pygame.draw.line(screen, DETECTOR_COLOR, self.p1.tuple(), self.p2.tuple(), 4)

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8

    def get_params_str(self):
        return [
            f"Detector: p1=({self.p1.x:.1f}, {self.p1.y:.1f})",
            f"p2=({self.p2.x:.1f}, {self.p2.y:.1f})",
            f"count={self.count}, power_sum={self.power_sum:.4f}"
        ]
