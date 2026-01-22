"""
Element loader / factory
-----------------------
This file allows a user to define optical elements in an external
parameter file (JSON or YAML), choose the appropriate element type,
and instantiate the correct Python objects.

Supported elements:
- Detector
- Lens (thin lens)
- CurvedLens (bulge-based)
- MediaInterface
- Mirror
- FiberSource (based on the last constructor you provided)

The only assumption is that a Vector class exists and can be
constructed as Vector(x, y).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


from components.element import OpticalElement
from components.sources.fiber import FiberSource 
from components.lens import Lens 
from components.detector import Detector
from components.media_interface import MediaInterface
from components.mirror import Mirror    
from core.vector import Vector


# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

def _make_vector(v: Any):
    """Create a Vector from [x, y] or (x, y)."""
    if v is None:
        return None
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise ValueError(f"Invalid vector format: {v}")
    return Vector(float(v[0]), float(v[1]))


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

class ElementFactory:
    """Factory that maps config entries to optical elements."""

    @staticmethod
    def create(cfg: Dict[str, Any]):
        etype = cfg.get("type")
        if etype is None:
            raise ValueError("Element config missing 'type'")

        etype = etype.lower()

        if etype == "detector":
            return Detector(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
            )

        if etype == "lens":
            return Lens(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                cfg.get("f", cfg.get("focal_length")),
            )

        if etype == "curvedlens":
            return Lens(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                bulge=cfg.get("bulge", 40.0),
            )

        if etype == "mediainterface":
            return MediaInterface(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                n1=cfg.get("n1", 1.0),
                n2=cfg.get("n2", 4.0),
            )

        if etype == "mirror":
            return Mirror(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
            )

        if etype == "fibersource":
            return FiberSource(
                pos_x=cfg["pos_x"],
                pos_y=cfg["pos_y"],
                mfd=cfg.get("mfd", 9.232917),
                cladding_diameter=cfg.get("cladding_diameter", 124.9329),
                n_core=cfg.get("n_core", 1.4527),
                cleave_angle=cfg.get("cleave_angle", -8.0),
                core_offset=tuple(cfg.get("core_offset", (0, 0))),
                angle_deg=cfg.get("angle_deg", 0.0),
                total_power=cfg.get("total_power", 1.0),
                wavelength=cfg.get("wavelength", 1.31),
            )

        raise ValueError(f"Unknown element type: {etype}")


# -----------------------------------------------------------------------------
# File loading
# -----------------------------------------------------------------------------

def load_elements(path: str | Path) -> List[Any]:
    """
    Load optical elements from a JSON or YAML file.

    File format example (JSON):
    ---------------------------
    [
      {
        "type": "Lens",
        "p1": [0, -5],
        "p2": [0,  5],
        "f": 25.0
      },
      {
        "type": "Detector",
        "p1": [50, -5],
        "p2": [50,  5]
      }
    ]
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    else:
        with path.open("r") as f:
            data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Top-level config must be a list of elements")

    elements = []
    for cfg in data:
        elements.append(ElementFactory.create(cfg))

    return elements


# -----------------------------------------------------------------------------
# Convenience
# -----------------------------------------------------------------------------

def load_scene(path: str | Path):
    """Alias for load_elements, semantic sugar."""
    return load_elements(path)
