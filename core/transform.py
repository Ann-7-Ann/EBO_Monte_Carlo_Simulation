def ray_to_theta(ray_dir, axis, normal):
    """
    Project 2D ray direction into paraxial angle
    """
    theta = ray_dir.dot(normal)
    return theta


def theta_to_dir(theta, axis, normal):
    """
    Convert paraxial angle back to 2D direction
    """
    d = axis + normal * theta
    return d.normalize()