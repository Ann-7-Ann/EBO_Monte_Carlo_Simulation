from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from components.detector import Detector
from simulation.tracer import trace_rays


@dataclass(frozen=True)
class ParamSpec:
    """Gaussian parameter specification (nominal + sigma)."""
    name: str
    nominal: float
    sigma: float
    unit: str = ""


# Default table from the shared spreadsheet screenshot.
# NOTE: Not all parameters are currently mapped to geometry/optics; we still
# sample and export them so the MC framework matches the table and can be
# refined incrementally.
DEFAULT_SPECS: list[ParamSpec] = [
    ParamSpec("n_adhesive1", 1.4898, 0.00000333, ""),
    ParamSpec("launch_MFD_1_um", 9.232917, 0.082087287, "um"),
    ParamSpec("launch_cladding_dia_1_um", 124.9329, 0.130657401, "um"),
    ParamSpec("core_clad_offset_launch_1_x_um", 0.0, 0.155024366, "um"),
    ParamSpec("cleave_angle_launch_1_deg", 8.0, 0.333333333, "deg"),
    ParamSpec("path_adhesive_launch_1_um", 65.0, 5.0, "um"),
    ParamSpec("angle_pedestal_ferrule1_deg", 0.0, 0.001, "deg"),
    ParamSpec("angle_wall_ferrule1_x_deg", 0.0, 0.001, "deg"),
    ParamSpec("angle_wall1_y_deg", -9.0, 0.001, "deg"),
    ParamSpec("path_lens1_um", 539.0, 0.2, "um"),
    ParamSpec("angle_lens1_deg", 47.0, 0.001, "deg"),
    ParamSpec("RoC_lens1_x_um", 823.0, 0.2, "um"),
    ParamSpec("RoC_lens1_y_um", 1755.0, 0.2, "um"),
    ParamSpec("offset_lens1_x_um", 0.0, 0.2, "um"),
    ParamSpec("offset_lens1_y_um", 0.439218, 0.2, "um"),
    ParamSpec("path_interface1_um", 567.0, 0.2, "um"),
]


@dataclass
class MonteCarloRow:
    trial: int
    seed_used: int
    rays_emitted: int
    p_in: float
    p_out: float
    il_db: float
    params: dict[str, float]


def _compute_il_db(p_in: float, p_out: float) -> float:
    if p_in <= 0 or p_out <= 0:
        return float("inf")
    ratio = p_out / p_in
    if ratio <= 0:
        return float("inf")
    return -10.0 * math.log10(ratio)


def _find_detector(detectors: list[Detector], label_substring: str) -> Detector | None:
    key = (label_substring or "").strip().lower()
    for d in detectors:
        if key and key in (d.label or "").lower():
            return d
    return None


def run_monte_carlo(
    *,
    scene,
    build_scene_for_params: Callable[[dict[str, float]], None],
    emit_rays: Callable[[Any], list],
    rng_manager,
    um_per_px: float,
    specs: list[ParamSpec] | None,
    trials: int,
    rays_cap: int,
    base_seed: int,
    sigma_scale: float,
    exports_dir: str,
) -> tuple[str, str, list[MonteCarloRow]]:
    """Run Monte Carlo parameter sampling and export CSV + histogram.

    - build_scene_for_params(sampled_params) must clear/rebuild the scene in-place.
    - emit_rays(rng) must emit rays for the current scene.
    - We compute IL using Output/Input detector power sums:
        IL = -10 log10(P_out / P_in)
    """
    specs = list(specs) if specs is not None else list(DEFAULT_SPECS)
    trials = int(max(1, trials))
    rays_cap = int(max(0, rays_cap))
    sigma_scale = float(sigma_scale)

    os.makedirs(exports_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(exports_dir, f"monte_carlo_{timestamp}.csv")
    hist_path = os.path.join(exports_dir, f"monte_carlo_il_hist_{timestamp}.png")
    summary_path = os.path.join(exports_dir, f"monte_carlo_summary_{timestamp}.txt")

    rows: list[MonteCarloRow] = []

    # Columns: fixed + all sampled params
    param_names = [s.name for s in specs]

    for i in range(trials):
        seed_used = int(base_seed) + i
        rng_manager.set_seed(seed_used)
        rng = rng_manager.rng()

        # Sample parameters
        sampled: dict[str, float] = {}
        for s in specs:
            sig = float(s.sigma) * sigma_scale
            if sig <= 0:
                sampled[s.name] = float(s.nominal)
            else:
                sampled[s.name] = float(rng.gauss(float(s.nominal), sig))

        # Basic physical clamps (avoid nonsense values)
        # n
        if "n_adhesive1" in sampled:
            sampled["n_adhesive1"] = max(1.0, sampled["n_adhesive1"])
        # lengths (um)
        for k in list(sampled.keys()):
            if k.endswith("_um") and "offset_" not in k:
                sampled[k] = max(0.0, sampled[k])

        # Rebuild scene with this sample
        build_scene_for_params(sampled)

        # Reset detectors
        for o in scene.objects:
            if isinstance(o, Detector):
                o.reset()

        # Emit + cap
        rays = emit_rays(rng)
        if rays_cap and len(rays) > rays_cap:
            rays = rays[:rays_cap]

        # Normalize total emitted power to 1.0
        p_emit = sum(getattr(r, "power", 1.0) for r in rays)
        if p_emit > 0:
            s = 1.0 / p_emit
            for r in rays:
                r.power = getattr(r, "power", 1.0) * s

        # Trace headless
        trace_rays(rays, scene, screen=None, um_per_px=um_per_px, draw=False)

        detectors = [o for o in scene.objects if isinstance(o, Detector)]
        det_in = _find_detector(detectors, "input") or (detectors[0] if detectors else None)
        det_out = _find_detector(detectors, "output") or (detectors[1] if len(detectors) > 1 else None)

        p_in = float(det_in.power_sum) if det_in is not None else 0.0
        p_out = float(det_out.power_sum) if det_out is not None else 0.0
        il_db = float(_compute_il_db(p_in, p_out))

        rows.append(
            MonteCarloRow(
                trial=i,
                seed_used=seed_used,
                rays_emitted=len(rays),
                p_in=p_in,
                p_out=p_out,
                il_db=il_db,
                params=sampled,
            )
        )

    # Export CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trial", "seed_used", "rays_emitted", "p_in", "p_out", "il_db", *param_names])
        for r in rows:
            w.writerow([
                r.trial,
                r.seed_used,
                r.rays_emitted,
                f"{r.p_in:.8f}",
                f"{r.p_out:.8f}",
                "inf" if math.isinf(r.il_db) else f"{r.il_db:.6f}",
                *[f"{r.params.get(n, float('nan')):.10g}" for n in param_names],
            ])

    # Summary stats + histogram
    il_vals = [r.il_db for r in rows if not math.isinf(r.il_db) and not math.isnan(r.il_db)]
    mean_il = sum(il_vals) / len(il_vals) if il_vals else float("inf")
    std_il = float("nan")
    if len(il_vals) >= 2:
        m = mean_il
        std_il = math.sqrt(sum((x - m) ** 2 for x in il_vals) / (len(il_vals) - 1))

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"Trials: {trials}\n")
        f.write(f"Finite IL count: {len(il_vals)}\n")
        f.write(f"Mean IL (dB): {mean_il if not math.isinf(mean_il) else 'inf'}\n")
        f.write(f"Std IL (dB): {std_il}\n")
        f.write(f"CSV: {csv_path}\n")
        f.write(f"Histogram: {hist_path}\n")
        f.write("\nApplied sampling (Gaussian):\n")
        for s in specs:
            pct = (abs(s.sigma) / abs(s.nominal) * 100.0) if abs(s.nominal) > 1e-12 else float("nan")
            f.write(f"- {s.name}: nominal={s.nominal} sigma={s.sigma} (≈{pct:.4g}% of nominal) unit={s.unit}\n")

    # Plot histogram (optional dependency)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure()
        if il_vals:
            plt.hist(il_vals, bins=min(50, max(10, int(math.sqrt(len(il_vals))))), edgecolor="black")
            plt.xlabel("Insertion Loss IL (dB)")
            plt.ylabel("Count")
            plt.title("Monte Carlo IL Histogram")
        else:
            plt.text(0.5, 0.5, "No finite IL values", ha="center", va="center")
            plt.axis("off")
        plt.tight_layout()
        plt.savefig(hist_path, dpi=160)
        plt.close()
    except Exception:
        # If matplotlib isn't available, skip plotting.
        pass

    return csv_path, summary_path, rows
