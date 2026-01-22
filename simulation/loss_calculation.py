import math
from media.medium import Medium  

def calculate_loss_db(power_in, distance_um, k_value, wavelength_um):
    """
    Calculates the optical loss in dB after traveling distance_um
    in a medium with extinction coefficient k.
    """
    medium = Medium(k=k_value, wavelength_um=wavelength_um)
    power_out = medium.apply_absorption(power_in, distance_um)

    if power_out <= 0.0:
        return float('inf')  # infinite loss if power goes to 0

    loss_db = 10 * math.log10(power_in / power_out)
    return loss_db
