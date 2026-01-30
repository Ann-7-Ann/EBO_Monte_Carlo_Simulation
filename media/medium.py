import math


class Medium:
    """Uniform medium model with Beer–Lambert absorption and refractive index.

    Parameters:
        n: refractive index (dimensionless).
        alpha_per_um: absorption coefficient in 1/µm.

    Power decays as:
        P_out = P_in * exp(-alpha_per_um * L_um)
    """

    def __init__(self, n: float = 1.0, alpha_per_um: float = 0.0, name: str = ""):
        self.n = float(n)
        self.name = str(name) if name is not None else ""
        self.alpha_per_um = float(alpha_per_um)

    def apply_absorption(self, power: float, distance_um: float) -> float:
        if power <= 0.0:
            return 0.0
        if self.alpha_per_um <= 0.0:
            return power
        x = -self.alpha_per_um * max(0.0, float(distance_um))
        if x < -700:
            return 0.0
        return power * math.exp(x)