import math
import random
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
        cleave_angle=-8.0,          # Fiber cleave angle in degrees
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


    def emit(self, num_rays=110):
        """
        Emit rays from the fiber end along the propagation axis.

        Parameters:
        - num_rays: number of rays across the mode field to simulate

        Returns:
        - List of Ray objects representing emitted rays
        """

        rays = []
        
        # Position of the ray at fiber exit (including offsets)
        x = self.pos.x + self.core_offset.x
        y = self.pos.y + self.core_offset.y

        # Approximate "waist" of the Gaussian mode (half the mode field diameter)
        waist = self.mfd / 2        # meters
        wavelength = 1.3e-6         # meters
        theta_div = wavelength / (math.pi * waist)  #angular standard deviation

        for _ in range(num_rays):
            # Gaussian transverse offset from fiber core center
            theta_spread = random.gauss(0, theta_div*1000000)

            # Launch angle (paraxial) includes cleave angle and small spread
            theta = self.angle + self.cleave_angle + theta_spread

            # Direction vector of the ray (unit vector)
            direction = Vector(
                math.cos(theta),
                math.sin(theta)
            )

            # Append the ray to the list
            rays.append(Ray(Vector(x, y), direction))

        return rays
