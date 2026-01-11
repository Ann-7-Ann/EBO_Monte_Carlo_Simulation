import numpy as np
from components.element import OpticalElement
from core.matrices import interface
from core.transform import ray_to_theta, theta_to_dir
from simulation.hittest import point_segment_distance


class MediaInterface(OpticalElement):
    """
    Represents a straight boundary between two optical media with
    refractive indices n1 and n2.
    """

    def __init__(self, p1, p2, n1, n2):
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
        """
        Computes how the ray direction changes when crossing the interface
        using Snell’s law in matrix form.
        """

        # Incoming ray direction vector
        direction = ray.dir

        # Unit vector along the interface
        axis = (self.p2 - self.p1).normalize()

        # Perpendicular (normal) to the interface
        normal = axis.perp()

        # Convert ray direction into an angle relative to the interface
        # (measured in the basis defined by axis and normal)
        theta = ray_to_theta(direction, axis, normal)

        # Interface matrix implementing Snell's law
        M = interface(self.n1, self.n2)

        # Apply the interface matrix to the ray angle
        # Input vector is [height, angle]; height is 0 at the interface
        _, theta2 = (M @ [[0], [theta]]).flatten()

        # Convert the refracted angle back into a direction vector
        return theta_to_dir(theta2, axis, normal)

    def contains_point(self, pos):
        """
        Returns True if a point is close enough to the interface segment.
        Used for hit testing and UI interaction.
        """
        return point_segment_distance(pos, self.p1, self.p2) < 8
