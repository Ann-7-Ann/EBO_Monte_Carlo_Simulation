import numpy as np
from components.element import OpticalElement
from core.matrices import interface
from core.transform import ray_to_theta, theta_to_dir
from simulation.hittest import point_segment_distance
import pygame
import math


class MediaInterface(OpticalElement):
    """
    Represents a straight boundary between two optical media with
    refractive indices n1 and n2.
    """

    def __init__(self, p1, p2, n1 = 1.0, n2 = 4.0):
        """
        p1, p2 : endpoints of the interface segment
        n1     : refractive index on the incident side
        n2     : refractive index on the transmitted side
        """
        self.p1 = p1
        self.p2 = p2
        self.n1 = n1
        self.n2 = n2

    def intersect(self, ray):
        """
        Computes the intersection between a ray and the interface segment.

        Returns hit information (or None) from ray_segment().
        """
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        d = ray.dir
        axis = (self.p2 - self.p1).normalize()
        normal = axis.perp()

        # Determine incident side
        dot = d.dot(normal)
        if abs(dot) < 1e-12:
            dot = 1e-12  # avoid zero
        if dot > 0:
            normal = -normal

        theta = ray_to_theta(d, axis, normal)

        M = interface(self.n1, self.n2)

        h, theta2 = (M @ [[0], [theta]]).flatten()
        
        return theta_to_dir(theta2, axis, normal)

    def contains_point(self, pos):
        """
        Returns True if a point is close enough to the interface segment.
        Used for hit testing and UI interaction.
        """
        return point_segment_distance(pos, self.p1, self.p2) < 8

    def draw(self, screen):
        # Optional: Draw the interface as a thin line for visualization
        pygame.draw.line(screen, (255, 255, 255), self.p1.tuple(), self.p2.tuple(), 1)

    def get_params_str(self):
        return [
            f"Interface:p1=({self.p1.x:.1f}, {self.p1.y:.1f})",
            f"p2=({self.p2.x:.1f}, {self.p2.y:.1f})",
            f"n1={self.n1:.2f}, n2={self.n2:.2f}"
        ]