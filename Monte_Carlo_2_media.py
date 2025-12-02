import numpy as np
import matplotlib.pyplot as plt

def monte_carlo_refraction(
    n1=1.0,               # refractive index of medium 1
    n2=1.5,               # refractive index of medium 2
    theta_inc_deg=30,     # nominal angle of incidence
    sigma_noise=2.0,      # random variation of angle (degrees)
    N=100000              # number of rays
):
    # Convert to radians
    theta_inc_nom = np.radians(theta_inc_deg)

    # Random perturbation of angle
    theta_inc = theta_inc_nom + np.radians(np.random.normal(0, sigma_noise, N))

    # Snell’s law
    #https://en.wikipedia.org/wiki/Snell%27s_law
    sin_theta_t = (n1 / n2) * np.sin(theta_inc)

    # Identify total internal reflection
    #https://en.wikipedia.org/wiki/Total_internal_reflection
    tir_mask = np.abs(sin_theta_t) > 1.0
    if np.all(tir_mask):
        raise RuntimeError("No transmission at all: all rays undergo total internal reflection")

    # Transmission angles
    theta_t = np.zeros_like(theta_inc)
    theta_t[~tir_mask] = np.arcsin(sin_theta_t[~tir_mask])

    # Fresnel reflectance
    R = np.zeros_like(theta_inc)
    # Fresnel equations
    #https://en.wikipedia.org/wiki/Fresnel_equations
    theta_i = theta_inc[~tir_mask]
    theta_tt = theta_t[~tir_mask]

    Rs = ((n1*np.cos(theta_i) - n2*np.cos(theta_tt)) /
          (n1*np.cos(theta_i) + n2*np.cos(theta_tt))) ** 2

    Rp = ((n1*np.cos(theta_tt) - n2*np.cos(theta_i)) /
          (n1*np.cos(theta_tt) + n2*np.cos(theta_i))) ** 2

    R[~tir_mask] = 0.5 * (Rs + Rp)

    # For TIR rays, reflectance = 1
    R[tir_mask] = 1.0

    # Fraction of transmitted power per ray
    transmitted_power = 1.0 - R[~tir_mask]
    # Insertion loss per ray in dB
    #https://en.wikipedia.org/wiki/Insertion_loss
    insertion_loss_per_ray_dB = -10 * np.log10(transmitted_power)

    best_ray_idx = np.argmin(insertion_loss_per_ray_dB)  
    worst_ray_idx = np.argmax(insertion_loss_per_ray_dB)

    return {
        "incident_angles_deg": np.degrees(theta_inc),
        "transmitted_angles_deg": np.degrees(theta_t),
        "R": R,
        "T": transmitted_power,
        "insertion_loss_per_ray_dB": insertion_loss_per_ray_dB,
        "best_ray_idx": best_ray_idx,
        "worst_ray_idx": worst_ray_idx
    }



result = monte_carlo_refraction(
    n1=1.5,       # glass
    n2=1.0,       # air
    theta_inc_deg=90,
    sigma_noise=5,
    N=50000
)

# Extract data
theta_inc = result["incident_angles_deg"]
theta_t = result["transmitted_angles_deg"]
reflactance = result["R"]
transmitivity = result["T"]
insertion_loss_dB = result["insertion_loss_per_ray_dB"]
best_idx = result["best_ray_idx"]
worst_idx = result["worst_ray_idx"]

# Histogram of insertion loss
plt.figure(figsize=(8,5))
plt.hist(insertion_loss_dB, bins=100, color='skyblue', edgecolor='k')
plt.axvline(insertion_loss_dB[best_idx], color='green', linestyle='--', label='Best Ray')
plt.axvline(insertion_loss_dB[worst_idx], color='red', linestyle='--', label='Worst Ray')
plt.xlabel("Insertion Loss (dB)")
plt.ylabel("Number of Rays")
plt.title("Distribution of Insertion Loss per Ray")
plt.legend()
plt.grid(True)
plt.show()

# Histogram of transmitted angles (exclude TIR rays)
theta_t_no_tir = theta_t[result["R"] < 1.0]  # only transmitted rays
plt.figure(figsize=(8,5))
plt.hist(theta_t_no_tir, bins=100, color='lightcoral', edgecolor='k')
plt.xlabel("Transmitted Angle (deg)")
plt.ylabel("Number of Rays")
plt.title("Distribution of Transmitted Angles")
plt.grid(True)
plt.show()

# Scatter plot: insertion loss vs incident angle
plt.figure(figsize=(8,5))
transmitted_mask = reflactance < 1.0  # only rays that actually transmit
plt.scatter(theta_inc[transmitted_mask], insertion_loss_dB, s=1, alpha=0.3, label='Rays')
plt.scatter(theta_inc[best_idx], insertion_loss_dB[best_idx], color='green', label='Best Ray', s=50)
plt.scatter(theta_inc[worst_idx], insertion_loss_dB[worst_idx], color='red', label='Worst Ray', s=50)
plt.xlabel("Incident Angle (deg)")
plt.ylabel("Insertion Loss (dB)")
plt.title("Insertion Loss vs Incident Angle")
plt.legend()
plt.grid(True)
plt.show()
