import math
import random
import numpy as np  
from core.vector import Vector
from core.ray import Ray
from core.transform import deg_to_rad
import pygame
from config import BEAM_COLOR
from components.media_interface import MediaInterface


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
        cladding_diameter=124.9329 , # Fiber cladding diameter
        n_core=1.4527,              # Refractive index of the fiber core
        cleave_angle=-8.0,           # Fiber cleave angle in degrees
        core_offset=(0, 0),        # Offset of core center from fiber geometric center
        angle_deg=0.0,             # Central launch angle (pedestal angle) in degrees
        total_power=1.0,
        wavelength = 1.31       
    ):
        # Position of fiber end
        self.pos = Vector(pos_x, pos_y)

        # Fiber parameters
        self.mfd = mfd
        self.cladding_diameter = cladding_diameter
        self.n_core = n_core

        # Cleave angle in radians
        self.cleave_angle = deg_to_rad(cleave_angle)

        # Core offset as a vector
        self.core_offset = Vector(*core_offset)

        # Central launch angle (pedestal) in radians
        self.angle = deg_to_rad(angle_deg)

        self.total_power = float(total_power)
        self.wavelength = wavelength

        # Unrotated facet relative to fiber center
        half_clad = self.cladding_diameter / 2
        p1_local = Vector(10, -half_clad)
        p2_local = Vector(10, half_clad)

        # Rotate by cleave angle
        cos_theta = math.cos(self.cleave_angle)
        sin_theta = math.sin(self.cleave_angle)

        p1_rot = Vector(
            p1_local.x * cos_theta - p1_local.y * sin_theta,
            p1_local.x * sin_theta + p1_local.y * cos_theta
        ) + self.pos

        p2_rot = Vector(
            p2_local.x * cos_theta - p2_local.y * sin_theta,
            p2_local.x * sin_theta + p2_local.y * cos_theta
        ) + self.pos

        # Set the facet with rotated coordinates
        self.facet = MediaInterface(
            p1=p1_rot,
            p2=p2_rot,
            n1=self.n_core,
            n2=1.5218
        )


    def emit(self, num_rays=110, ray_id_start=0):
        """
        Emit rays from the fiber end along the propagation axis.

        Parameters:
        - num_rays: number of rays across the mode field to simulate

        Returns:
        - List of Ray objects representing emitted rays
        """

        rays = []
        if num_rays <= 0:
            return rays
        
        # Position of the ray at fiber exit (including offsets)
        x = self.pos.x + self.core_offset.x
        y = self.pos.y + self.core_offset.y

        # Approximate "waist" of the Gaussian mode (half the mode field diameter)
        waist = self.mfd / 2        # meters
        theta_div = self.wavelength / (math.pi * waist)  #angular standard deviation


        for i in range(num_rays):
            # Gaussian transverse offset from fiber core center
            theta_spread = random.gauss(0, theta_div)

            # Launch angle (paraxial) includes small spread
            theta = self.angle +  theta_spread

            # Direction vector of the ray (unit vector)
            direction = Vector(
                math.cos(theta),
                math.sin(theta)
            )

            # Append the ray to the list
            
            rays.append(
                Ray(
                    Vector(x, y),
                    direction,
                    ray_id=ray_id_start + i,
                    power=self.gaussian_pdf(theta_spread, theta_spread)
                )
            )

        return rays
    
    def gaussian_pdf(self, x, sigma):
        return math.exp(-(x*x) / (2*sigma*sigma))

    def draw(self, screen):
        pygame.draw.circle(screen, BEAM_COLOR, (self.pos.x, self.pos.y), 5)

    
    def get_params_str(self):
            return [
                f"Fiber: pos=({self.pos.x:.1f}, {self.pos.y:.1f})",
                f"mfd={self.mfd:.2f}, cladding_d={self.cladding_diameter:.2f}",
                f"n_core={self.n_core:.3f}, cleave_angle={math.degrees(self.cleave_angle):.1f}°",
                f"core_offset=({self.core_offset.x:.2f}, {self.core_offset.y:.2f})",
                f"angle={math.degrees(self.angle):.1f}°",
                f"power={self.total_power:.4f}"
            ]

    def contains_point(self, pos: Vector):
        return (pos - self.pos).length() < 10


    def sample_fiber_params(self):
        return {
            "mfd": np.random.normal(self.mfd, 0.082087287),
            "cladding_diameter": np.random.normal(self.cladding_diameter, 0.130657401),
            "cleave_angle": np.random.normal(self.cleave_angle, 1/3),  
            "core_offset": (np.random.normal(self.core_offset.x, 0.155024366)),
            "angle": np.random.normal(self.angle, 0.001),  
        }
