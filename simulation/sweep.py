from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import math

from components.detector import Detector
from simulation.tracer import trace_rays


@dataclass
class SweepResultRow:
    step: int
    param_value: float
    rays_emitted: int
    rays_detected: int
    p_detected: float
    il_db: float
    seed_used: int


def _compute_detector_union(detectors: list[Detector]) -> tuple[int, float]:
    """Return (unique_ray_count, union_power_sum)."""
    union_ids: set[int] = set()
    union_power = 0.0
    for d in detectors:
        for rid, pw in d.power_by_ray_id.items():
            if rid not in union_ids:
                union_ids.add(rid)
                union_power += pw
    return len(union_ids), union_power


def run_sweep(
    *,
    scene,
    emit_rays: Callable[[Any], list],
    rng_manager,
    um_per_px: float,
    target_name: str,
    get_param: Callable[[], float],
    set_param: Callable[[float], None],
    start: float,
    stop: float,
    step: float,
    rays_per_step_cap: int,
    base_seed: int,
    exports_dir: str,
) -> tuple[str, list[SweepResultRow]]:
    """Run a simple 1D parameter sweep and export CSV.

    Notes:
    - `emit_rays(rng)` should emit rays for the current scene, using the provided RNG.
    - `rays_per_step_cap` is applied as a hard cap to keep runtime predictable.
    """

    step = float(step) if step is not None else 0.0
    if abs(step) < 1e-12:
        raise ValueError("Sweep step must be non-zero")

    # Build value list (inclusive stop)
    values: list[float] = []
    if step > 0:
        v = float(start)
        while v <= float(stop) + 1e-12:
            values.append(v)
            v += step
    else:
        v = float(start)
        while v >= float(stop) - 1e-12:
            values.append(v)
            v += step

    os.makedirs(exports_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(exports_dir, f"sweep_{target_name}_{timestamp}.csv")

    original_value = get_param()
    rows: list[SweepResultRow] = []

    try:
        for i, val in enumerate(values):
            set_param(val)
            seed_used = int(base_seed) + i
            rng_manager.set_seed(seed_used)
            rng = rng_manager.rng()

            # reset detectors
            for o in scene.objects:
                if isinstance(o, Detector):
                    o.reset()

            rays = emit_rays(rng)
            if rays_per_step_cap and len(rays) > int(rays_per_step_cap):
                rays = rays[: int(rays_per_step_cap)]

            # Normalize total emitted power to 1.0
            p_emit = sum(getattr(r, "power", 1.0) for r in rays)
            if p_emit > 0:
                scale = 1.0 / p_emit
                for r in rays:
                    r.power = getattr(r, "power", 1.0) * scale
                p_emit = 1.0

            # Trace headless
            trace_rays(rays, scene, screen=None, um_per_px=um_per_px, draw=False)

            detectors = [o for o in scene.objects if isinstance(o, Detector)]
            det_count, det_power = _compute_detector_union(detectors)

            ratio = det_power / p_emit if p_emit > 0 else 0.0
            il_db = float("inf") if ratio <= 0 else -10.0 * math.log10(ratio)

            rows.append(
                SweepResultRow(
                    step=i,
                    param_value=float(val),
                    rays_emitted=len(rays),
                    rays_detected=det_count,
                    p_detected=float(det_power),
                    il_db=float(il_db),
                    seed_used=seed_used,
                )
            )

    finally:
        # Restore original param
        try:
            set_param(original_value)
        except Exception:
            pass

    # Write CSV
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "target",
            "step",
            "param_value",
            "rays_emitted",
            "rays_detected_unique",
            "p_detected",
            "il_db",
            "seed_used",
        ])
        for r in rows:
            w.writerow([
                target_name,
                r.step,
                r.param_value,
                r.rays_emitted,
                r.rays_detected,
                f"{r.p_detected:.8f}",
                "inf" if math.isinf(r.il_db) else f"{r.il_db:.6f}",
                r.seed_used,
            ])

    return out_path, rows
