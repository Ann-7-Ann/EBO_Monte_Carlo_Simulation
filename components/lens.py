import pygame
import numpy as np
from components.element import OpticalElement
from core.matrices import thin_lens
from core.transform import ray_to_theta, theta_to_dir
from config import LENS_COLOR
from simulation.hittest import point_segment_distance

class Lens(OpticalElement):
    def __init__(self, p1, p2, f):
        self.p1 = p1
        self.p2 = p2
        self.f = f

    def intersect(self,  ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, direction, hit):
        axis = (self.p2 - self.p1).normalize()
        normal = axis.perp()

        y = (hit - self.p1).dot(normal)
        theta = ray_to_theta(direction, axis, normal)

        M = thin_lens(self.f)
        y2, theta2 = (M @ [[y], [theta]]).flatten()
        
        return theta_to_dir(theta2, axis, normal)

    def draw(self, screen):
        pygame.draw.line(screen, LENS_COLOR, self.p1.tuple(), self.p2.tuple(), 2)

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8
