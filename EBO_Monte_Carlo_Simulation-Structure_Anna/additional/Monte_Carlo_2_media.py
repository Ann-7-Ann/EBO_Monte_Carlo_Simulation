import numpy as np
import matplotlib.pyplot as plt


def snell_matrix(n1, n2):
    """Refraction at a flat interface"""
    return np.array([
        [1.0,       0.0],
        [0.0,  n1/n2]
    ])

def apply_refraction_matrix(theta_inc, n1, n2):
    """Apply Snell's law via matrix multiplication."""
    M = snell_matrix(n1, n2)
    # Build ray vector [x, theta]; x=0 for flat interface
    vec = np.vstack((np.zeros_like(theta_inc), theta_inc))
    out = M @ vec
    sin_theta_t = out[1]

    # Handle total internal reflection
    tir_mask = np.abs(sin_theta_t) > 1.0
    theta_t = np.zeros_like(theta_inc)
    theta_t[~tir_mask] = np.arcsin(sin_theta_t[~tir_mask])

    return theta_t, tir_mask


def monte_carlo_refraction(
    n1=1.0,               # refractive index of medium 1
    n2=1.5,               # refractive index of medium 2
    theta_inc_deg=30,     # nominal angle of incidence
    wavelength= 1.55e-6,   # meters
    MFD=10e-6,             # mode field diameter in meters
    N=100000              # number of rays
):
    
    #angular width
    #https://en.wikipedia.org/wiki/Gaussian_beam
    theta_mdf = 2 * wavelength / (np.pi * MFD)
    # Convert to radians
    theta_inc_nom = np.radians(theta_inc_deg)

    # Random perturbation of angle
    theta_inc = theta_inc_nom + np.random.normal(0, theta_mdf, N)

    # Snell’s law
    #https://en.wikipedia.org/wiki/Snell%27s_law
    #sin_theta_t = (n1 / n2) * np.sin(theta_inc)

    # Identify total internal reflection
    #https://en.wikipedia.org/wiki/Total_internal_reflection
    #tir_mask = np.abs(sin_theta_t) > 1.0
    #if np.all(tir_mask):
        #raise RuntimeError("No transmission at all: all rays undergo total internal reflection")
    # Transmission angles
    #theta_t = np.zeros_like(theta_inc)
    #theta_t[~tir_mask] = np.arcsin(sin_theta_t[~tir_mask])   
    
      
    # Use matrix Snell calculation
    theta_t, tir_mask = apply_refraction_matrix(theta_inc, n1, n2)


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
    T = 1.0 - R

    #https://en.wikipedia.org/wiki/Insertion_loss
   
   #Mode weights
    weights = np.exp(-2 * ((theta_inc - theta_inc_nom) / theta_mdf)**2)

    # Weighted total transmission (mode-matched)
    weighted_T = np.sum(weights * T) / np.sum(weights)
    weighted_IL_dB = -10 * np.log10(weighted_T)

    return {
        "incident_angles_deg": np.degrees(theta_inc),
        "transmitted_angles_deg": np.degrees(theta_t),
        "R": R,
        "T": T,
        "weights": weights,
        "weighted_IL_dB": weighted_IL_dB,
    }



result = monte_carlo_refraction(
    n1=1.46,
    n2=1.0,
    theta_inc_deg=8,
    wavelength=1.55e-6,
    MFD=10e-6,
    N=50000
)

plt.figure(figsize=(12,5))

# --- Left subplot: Histogram ---
plt.subplot(1,2,1)
plt.hist(result["incident_angles_deg"], bins=200, edgecolor='k')
plt.xlabel("Incident Angle (deg)")
plt.ylabel("Count")
plt.title("Incident Angle Distribution")
plt.grid(True)

# --- Right subplot: Scatter + text ---
plt.subplot(1,2,2)
plt.scatter(result["incident_angles_deg"], result["T"], s=1, alpha=0.3)
plt.xlabel("Incident Angle (deg)")
plt.ylabel("Transmittance T")
plt.title("Transmittance vs Incident Angle")
plt.grid(True)

plt.text(
    0.52, 0.15,
    f"Weighted IL = {result['weighted_IL_dB']:.4f} dB",
    transform=plt.gca().transAxes,
    fontsize=12,
    verticalalignment='top'
)

plt.tight_layout()
plt.show()
