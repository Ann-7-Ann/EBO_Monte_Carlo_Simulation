import json
from pathlib import Path

from components.mirror import Mirror
from components.lensed_mirror import LensedMirror
from components.lens import Lens
from components.detector import Detector
from components.media_interface import MediaInterface
from components.sources.beam import Beam
from components.sources.fiber import FiberSource


# -------------------------
# Object → dict conversion
# -------------------------

def element_to_dict(obj):
    """Convert a scene object into a JSON-serializable dict."""

    # --- Detector ---
    if isinstance(obj, Detector):
        return {
            "type": "Detector",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
        }

    # --- Mirror ---
    if isinstance(obj, Mirror) and not isinstance(obj, LensedMirror):
        return {
            "type": "Mirror",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
        }

    # --- Lensed mirror ---
    if isinstance(obj, LensedMirror):
        return {
            "type": "LensedMirror",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
            "bulge": obj.bulge,
        }

    # --- Lens ---
    if isinstance(obj, Lens):
        return {
            "type": "Lens",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
            "f": obj.f,
        }

    # --- Media interface ---
    if isinstance(obj, MediaInterface):
        return {
            "type": "MediaInterface",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
            "n1": obj.n1,
            "n2": obj.n2,
        }

    # --- Beam ---
    if isinstance(obj, Beam):
        return {
            "type": "Beam",
            "p1": [obj.p1.x, obj.p1.y],
            "p2": [obj.p2.x, obj.p2.y],
            "spread_deg": obj.spread_deg,
            "pos_spacing_px": obj.pos_spacing_px,
            "angle_samples": obj.angle_samples,
            "total_power": obj.total_power,
        }

    # --- Fiber source ---
    if isinstance(obj, FiberSource):
        return {
            "type": "FiberSource",
            "pos_x": obj.pos_x,
            "pos_y": obj.pos_y,
            "mfd": obj.mfd,
            "cladding_diameter": obj.cladding_diameter,
            "n_core": obj.n_core,
            "cleave_angle": obj.cleave_angle,
            "core_offset": list(obj.core_offset),
            "angle_deg": obj.angle_deg,
            "total_power": obj.total_power,
            "wavelength": obj.wavelength,
        }

    return None

def scene_to_dict(scene):
    """Convert entire scene into a list of element dicts."""
    elements = []

    for obj in scene.objects:
        # Skip auto-generated helpers (like fiber facet)
        if hasattr(obj, "is_helper") and obj.is_helper:
            continue

        data = element_to_dict(obj)
        if data is not None:
            elements.append(data)

    return elements


def save_scene(scene, path):
    """Save scene to JSON file."""
    data = scene_to_dict(scene)

    path = Path(path)
    with path.open("w") as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Scene saved to {path}")
