import pygame
from components.element import OpticalElement
from config import MIRROR_COLOR
from simulation.hittest import point_segment_distance

class Boundary(OpticalElement):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, direction, hit):
        # Return None to stop the ray (no reflection)
        return None

    def draw(self, screen):
        pygame.draw.line(screen, (255, 255, 255), self.p1.tuple(), self.p2.tuple(), 1)
    
    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8