import math
from core.vector import Vector
from core.ray import Ray
from core.transform import deg_to_rad


class FiberSource:
    """
    Represents a fiber optic source emitting rays with a Gaussian-like 
    transverse distribution (mode field) from a cleaved fiber end.
    """

    def __init__(
        self,
        pos_x,                     # Fiber end position along propagation axis (x)
        pos_y,                     # Fiber end transverse position (y)
        mfd=9.232917,              # Mode field diameter of the fiber core
        cladding_diameter=124.9329,# Fiber cladding diameter
        n_core=1.4527,             # Refractive index of the fiber core
        cleave_angle=8.0,          # Fiber cleave angle in degrees
        core_offset=(0, 0),        # Offset of core center from fiber geometric center
        angle_deg=0.0,             # Central launch angle (pedestal angle) in degrees
    ):
        # Position of fiber end
        self.pos = Vector(pos_x, pos_y)

        # Fiber parameters
        self.mfd = mfd
        self.cladding_diameter = cladding_diameter
        self.n_core = n_core

        # Cleave angle in radians
        self.cleave_angle = deg_to_rad(self, cleave_angle)

        # Core offset as a vector
        self.core_offset = Vector(*core_offset)

        # Central launch angle (pedestal) in radians
        self.angle = deg_to_rad(self, angle_deg)


    def emit(self, num_rays=11):
        """
        Emit rays from the fiber end along the propagation axis.

        Parameters:
        - num_rays: number of rays across the mode field to simulate

        Returns:
        - List of Ray objects representing emitted rays
        """

        rays = []

        # Approximate "waist" of the Gaussian mode (half the mode field diameter)
        waist = self.mfd / 2

        for i in range(num_rays):
            # u ranges from -1 to 1 across the mode field
            u = (i / (num_rays - 1)) * 2 - 1 if num_rays > 1 else 0

            # Transverse position of this ray
            # Offset by fiber position, mode displacement
            y = self.pos.y + u * waist 
            x = self.pos.x

            # Paraxial launch angle
            # Combines the central angle, cleave angle, and small angular spread due to mode
            theta = self.angle + self.cleave_angle + u * (waist / self.mfd)

            # Direction vector of the ray (unit vector)
            direction = Vector(
                math.cos(theta),
                math.sin(theta)
            )

            # Append the ray to the list
            rays.append(Ray(Vector(x, y), direction))

        return rays
