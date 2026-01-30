import pygame

from components.element import OpticalElement
from core.vector import Vector
from media.medium import Medium


class MediaPolygon:
    """A polygonal region with its own refractive index and absorption.

    This is NOT an OpticalElement (it doesn't 'bounce' rays). Instead, rays
    refract when they cross its boundary, and absorb power while traveling
    inside.
    """

    def __init__(self, points: list[Vector], n: float = 1.0, alpha_per_um: float = 0.0, name: str = "media"):
        self.points: list[Vector] = list(points)
        self.medium = Medium(n=n, alpha_per_um=alpha_per_um, name=name)

        # Visuals
        self.fill_rgba = (34, 197, 94, 35)    # green, translucent
        self.border_rgb = (34, 197, 94)
        self.vertex_rgb = (167, 139, 250)
        self.vertex_r = 5

    def move(self, dx: float, dy: float):
        self.points = [Vector(p.x + dx, p.y + dy) for p in self.points]

    def vertex_hit(self, pos: Vector, radius: float = 10.0):
        for i, p in enumerate(self.points):
            if (pos - p).length() <= radius:
                return i
        return None

    def contains_point(self, pos: Vector) -> bool:
        """Even-odd ray casting test."""
        pts = self.points
        if len(pts) < 3:
            return False
        x, y = pos.x, pos.y
        inside = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i].x, pts[i].y
            xj, yj = pts[j].x, pts[j].y
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
            )
            if intersect:
                inside = not inside
            j = i
        return inside

    def draw(self, screen):
        if len(self.points) >= 3:
            # Fill on a transparent overlay surface so alpha works.
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(overlay, self.fill_rgba, [p.tuple() for p in self.points])
            screen.blit(overlay, (0, 0))
            pygame.draw.polygon(screen, self.border_rgb, [p.tuple() for p in self.points], 2)
        elif len(self.points) == 2:
            pygame.draw.line(screen, self.border_rgb, self.points[0].tuple(), self.points[1].tuple(), 2)
        elif len(self.points) == 1:
            pygame.draw.circle(screen, self.border_rgb, self.points[0].tuple(), 3)

        # Vertex handles
        for p in self.points:
            pygame.draw.circle(screen, self.vertex_rgb, p.tuple(), self.vertex_r)

    def get_params_str(self):
        return [
            f"MediaPolygon: {self.medium.name} | vertices={len(self.points)}",
            f"n={self.medium.n:.4f}",
            f"alpha={self.medium.alpha_per_um:.6g} 1/µm",
        ]