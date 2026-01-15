import math


_EPS = 1e-12


def ray_to_theta(ray_dir, axis, normal):
    """Project 2D ray direction into paraxial slope theta.

    We interpret `axis` as the optical axis and `normal` as the transverse axis.
    For small angles, theta is the transverse slope relative to the axis:

        theta ≈ (ray·normal) / (ray·axis)

    This is more stable than using ray·normal directly.
    """

    denom = ray_dir.dot(axis)
    if abs(denom) < _EPS:
        # Nearly perpendicular to the optical axis; fall back to signed projection.
        return ray_dir.dot(normal)
    return ray_dir.dot(normal) / denom


def theta_to_dir(theta, axis, normal):
    """Convert paraxial slope theta back to a normalized 2D direction."""
    d = axis + normal * theta
    return d.normalize()


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)
