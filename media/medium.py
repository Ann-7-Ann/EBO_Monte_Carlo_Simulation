import math


class Medium:
    """
    Uniform medium with Beer–Lambert absorption using
    the optical extinction coefficient k.

    alpha = 4πk / λ
    """

    def __init__(self, k: float, wavelength_um: float):
        self.k = float(k)
        self.wavelength_um = float(wavelength_um)

        # Convert k -> absorption coefficient (1/µm)
        self.alpha_per_um = 4 * math.pi * self.k / self.wavelength_um

    def apply_absorption(self, power: float, distance_um: float) -> float:
        if power <= 0.0:
            return 0.0
        if self.alpha_per_um <= 0.0:
            return power

        x = -self.alpha_per_um * max(0.0, distance_um)
        if x < -700:
            return 0.0
        return power * math.exp(x)
