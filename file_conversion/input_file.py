"""
Element loader / factory
-----------------------
Load optical elements from a JSON scene file and instantiate
the correct Python objects.

Assumptions:
- All distances are in microns (µm)
- All angles in JSON are in degrees
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

from core.vector import Vector

from components.detector import Detector
from components.lens import Lens
from components.media_interface import MediaInterface
from components.media_polygon import MediaPolygon
from components.mirror import Mirror
from components.lensed_mirror import LensedMirror
from components.sources.beam import Beam
from components.sources.fiber import FiberSource


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def _make_vector(v: Any) -> Vector:
    """Create a Vector from [x, y]."""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise ValueError(f"Invalid vector format: {v}")
    return Vector(float(v[0]), float(v[1]))


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

class ElementFactory:
    """Factory mapping config entries to optical elements."""

    @staticmethod
    def create(cfg: Dict[str, Any]):
        etype = cfg.get("type")
        if not etype:
            raise ValueError("Element config missing 'type'")

        etype = etype.lower()

        # ------------------------------------------------------------------
        # Detector
        # ------------------------------------------------------------------
        if etype == "detector":
            return Detector(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
            )

        # ------------------------------------------------------------------
        # Lens
        # ------------------------------------------------------------------
        if etype == "lens":
            return Lens(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                float(cfg["f"]),
            )

        # ------------------------------------------------------------------
        # Media interface
        # ------------------------------------------------------------------
        if etype == "mediainterface":
            return MediaInterface(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                n1=float(cfg.get("n1", 1.0)),
                n2=float(cfg.get("n2", 1.0)),
            )

        # ------------------------------------------------------------------
        # Media polygon
        # ------------------------------------------------------------------
        if etype == "mediapolygon":
            return MediaPolygon(
                points=[_make_vector(p) for p in cfg["points"]],
                n=float(cfg.get("n", 1.0)),
                alpha_per_um=float(cfg.get("alpha_per_um", 0.0)),
            )

        # ------------------------------------------------------------------
        # Mirror
        # ------------------------------------------------------------------
        if etype == "mirror":
            return Mirror(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
            )

        # ------------------------------------------------------------------
        # Lensed mirror
        # ------------------------------------------------------------------
        if etype == "lensedmirror":
            return LensedMirror(
                _make_vector(cfg["p1"]),
                _make_vector(cfg["p2"]),
                bulge=float(cfg["bulge"]),
            )

        # ------------------------------------------------------------------
        # Beam
        # ------------------------------------------------------------------
        if etype == "beam":
            return Beam(
                p1=_make_vector(cfg["p1"]),
                p2=_make_vector(cfg["p2"]),
                spread_deg=float(cfg.get("spread_deg", 0.0)),
                pos_spacing_px=float(cfg.get("pos_spacing_px", 1.0)),
                angle_samples=int(cfg.get("angle_samples", 1)),
                total_power=float(cfg.get("total_power", 1.0)),
            )

        # ------------------------------------------------------------------
        # Fiber source
        # ------------------------------------------------------------------
        if etype == "fibersource":
            return FiberSource(
                pos_x=float(cfg["pos_x"]),
                pos_y=float(cfg["pos_y"]),
                mfd=float(cfg.get("mfd", 9.23)),
                cladding_diameter=float(cfg.get("cladding_diameter", 125.0)),
                n_core=float(cfg.get("n_core", 1.45)),
                cleave_angle=math.radians(cfg.get("cleave_angle_deg", 0.0)),
                core_offset=tuple(cfg.get("core_offset", (0, 0))),
                angle_deg=math.radians(cfg.get("angle_deg", 0.0)),
                total_power=float(cfg.get("total_power", 1.0)),
                wavelength=float(cfg.get("wavelength", 1.31)),
                n_out=float(cfg.get("n_out", 1.0)),
            )

        raise ValueError(f"Unknown element type: {etype}")


# -----------------------------------------------------------------------------
# File loading
# -----------------------------------------------------------------------------

def load_elements(path: str | Path) -> List[Any]:
    """Load optical elements from a JSON scene file."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Scene file must contain a list of elements")

    return [ElementFactory.create(cfg) for cfg in data]


# -----------------------------------------------------------------------------
# Convenience
# -----------------------------------------------------------------------------

def load_scene(path: str | Path):
    """Alias for load_elements."""
    return load_elements(path)
