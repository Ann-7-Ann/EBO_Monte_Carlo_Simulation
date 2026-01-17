import math


class Medium:
    """Uniform medium model with Beer-Lambert absorption.

    Parameters:
        alpha_per_um: absorption coefficient in 1/µm.
            Power decays as: P_out = P_in * exp(-alpha * L_um)

    Notes:
        If you later want to use the optical extinction coefficient `k`
        (imag part of refractive index), you can convert using:
            alpha = 4πk / λ
        (requires wavelength λ in the same length units).
    """

    def __init__(self, alpha_per_um: float = 0.0):
        self.alpha_per_um = float(alpha_per_um)

    def apply_absorption(self, power: float, distance_um: float) -> float:
        if power <= 0.0:
            return 0.0
        if self.alpha_per_um <= 0.0:
            return power
        # Guard against extreme exponent overflow.
        x = -self.alpha_per_um * max(0.0, distance_um)
        if x < -700:
            return 0.0
        return power * math.exp(x)
