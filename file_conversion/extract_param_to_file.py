import json
from pathlib import Path
import math

from components.mirror import Mirror
from components.lensed_mirror import LensedMirror
from components.lens import Lens
from components.detector import Detector
from components.media_interface import MediaInterface
from components.sources.beam import Beam
from components.sources.fiber import FiberSource
from components.media_polygon import MediaPolygon


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def vec2list(v):
    """Convert Vector → JSON-safe [x, y]."""
    return [float(v.x), float(v.y)]


# ---------------------------------------------------------------------
# Object → dict conversion
# ---------------------------------------------------------------------

def element_to_dict(obj):
    """Convert a scene object into a JSON-serializable dict."""

    # --- Detector ---
    if isinstance(obj, Detector):
        return {
            "type": "Detector",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
        }

    # --- Mirror ---
    if isinstance(obj, Mirror) and not isinstance(obj, LensedMirror):
        return {
            "type": "Mirror",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
        }

    # --- Lensed mirror ---
    if isinstance(obj, LensedMirror):
        return {
            "type": "LensedMirror",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
            "bulge": float(obj.bulge),
        }

    # --- Lens ---
    if isinstance(obj, Lens):
        return {
            "type": "Lens",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
            "f": float(obj.f),
        }

    # --- Media interface ---
    if isinstance(obj, MediaInterface):
        return {
            "type": "MediaInterface",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
            "n1": float(obj.n1),
            "n2": float(obj.n2),
        }

    # --- Media polygon ---
    if isinstance(obj, MediaPolygon):
        return {
            "type": "MediaPolygon",
            "points": [vec2list(p) for p in obj.points],
            "n": float(obj.medium.n),
            "alpha_per_um": float(obj.medium.alpha_per_um),
        }

    # --- Beam ---
    if isinstance(obj, Beam):
        return {
            "type": "Beam",
            "p1": vec2list(obj.p1),
            "p2": vec2list(obj.p2),
            "spread_deg": float(obj.spread_deg),
            "pos_spacing_px": float(obj.pos_spacing_px),
            "angle_samples": int(obj.angle_samples),
            "total_power": float(obj.total_power),
        }

    # --- Fiber source ---
    if isinstance(obj, FiberSource):
        return {
            "type": "FiberSource",
            "pos_x": float(obj.pos.x),
            "pos_y": float(obj.pos.y),
            "mfd": float(obj.mfd),
            "cladding_diameter": float(obj.cladding_diameter),
            "n_core": float(obj.n_core),
            "cleave_angle_deg": math.degrees(obj.cleave_angle),
            "core_offset": vec2list(obj.core_offset),
            "angle_deg": math.degrees(obj.angle),
            "total_power": float(obj.total_power),
            "wavelength": float(obj.wavelength),
            "n_out": float(obj.n_out),
        }

    return None


# ---------------------------------------------------------------------
# Scene → dict
# ---------------------------------------------------------------------

def scene_to_dict(scene):
    """Convert entire scene into a list of element dicts."""
    elements = []

    for obj in scene.objects:
        # Skip auto-generated helpers (e.g., fiber facets)
        if getattr(obj, "is_helper", False):
            continue

        data = element_to_dict(obj)
        if data is not None:
            elements.append(data)

    return elements


# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------

def save_scene(scene, path):
    """Save scene to JSON file."""
    data = scene_to_dict(scene)

    path = Path(path)
    with path.open("w") as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Scene saved to {path}")
