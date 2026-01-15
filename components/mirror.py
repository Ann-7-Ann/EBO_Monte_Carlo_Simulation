import pygame
from components.element import OpticalElement
from core.vector import Vector
from config import MIRROR_COLOR
from simulation.hittest import point_segment_distance

class Mirror(OpticalElement):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def normal(self):
        return (self.p2 - self.p1).perp().normalize()

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        """Specular reflection from a flat mirror."""
        direction = ray.dir
        n = self.normal()
        return direction - n * 2 * direction.dot(n)

    def draw(self, screen):
        pygame.draw.line(screen, MIRROR_COLOR, self.p1.tuple(), self.p2.tuple(), 3)
    
    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8
