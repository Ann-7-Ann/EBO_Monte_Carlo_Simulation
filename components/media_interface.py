import numpy as np
from components.element import OpticalElement
from core.matrices import interface
from core.transform import ray_to_theta, theta_to_dir
from simulation.hittest import point_segment_distance

class MediaInterface(OpticalElement):
    def __init__(self, p1, p2, n1, n2):
        self.p1 = p1
        self.p2 = p2
        self.n1 = n1
        self.n2 = n2

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, direction, hit):
        axis = (self.p2 - self.p1).normalize()
        normal = axis.perp()

        theta = ray_to_theta(direction, axis, normal)

        M = interface(self.n1, self.n2)
        _, theta2 = (M @ [[0], [theta]]).flatten()

        return theta_to_dir(theta2, axis, normal)


    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8
