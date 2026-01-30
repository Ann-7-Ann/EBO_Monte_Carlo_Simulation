import math

from core.vector import Vector


def reflect_dir(i: Vector, n: Vector) -> Vector:
    """Reflect incident direction `i` about surface normal `n`.

    Returns a unit direction.
    """
    i = i.normalize()
    n = n.normalize()
    return (i - n * (2.0 * i.dot(n))).normalize()


def refract_or_reflect(i: Vector, n: Vector, n1: float, n2: float):
    """Refract incident direction using Snell's law (2D).

    The normal does not need a consistent orientation; if it points in the
    "wrong" direction relative to the incident ray, we flip it.

    NOTE: We do NOT swap (n1,n2) here; callers must provide the correct
    incident/exit indices. This avoids incorrect TIR when the surface normal
    is oriented from medium1→medium2.

    Returns:
        (new_dir, did_reflect) where did_reflect is True for TIR.
    """
    i = i.normalize()
    n = n.normalize()

    # Ensure normal opposes the incident direction.
    if i.dot(n) > 0.0:
        n = n * -1.0

    if n2 == 0.0:
        return reflect_dir(i, n), True

    eta = float(n1) / float(n2)
    cos_i = -i.dot(n)
    cos_i = max(-1.0, min(1.0, cos_i))

    k = 1.0 - eta * eta * (1.0 - cos_i * cos_i)
    if k < 0.0:
        # Total internal reflection
        return reflect_dir(i, n), True

    t = i * eta + n * (eta * cos_i - math.sqrt(k))
    return t.normalize(), False