import os
import pygame

 # Heavy plotting deps (numpy/matplotlib) are imported lazily in export_profile_plots

from components.element import OpticalElement
from config import DETECTOR_COLOR
from simulation.hittest import point_segment_distance


class Detector(OpticalElement):
    """A segment detector.

    Behavior:
    - pass-through: does not change direction
    - unique counting: each ray is counted only once per frame (by ray_id)
    - power accumulation: sums power at first intersection (used for IL)
    """

    def __init__(self, p1, p2, label: str = ""):
        self.p1 = p1
        self.p2 = p2
        self.label = str(label) if label is not None else ""
        self._seen_ray_ids: set[int] = set()
        self._power_by_ray_id: dict[int, float] = {}  # ray_id -> power at first hit
        # 2.5D beam profile samples: ray_id -> (x_px_along_detector, u_px_out_of_plane, power)
        self._profile_by_ray_id: dict[int, tuple[float, float, float]] = {}

    @property
    def count(self) -> int:
        return len(self._seen_ray_ids)

    @property
    def power_sum(self) -> float:
        return float(sum(self._power_by_ray_id.values()))

    @property
    def power_by_ray_id(self) -> dict[int, float]:
        """Mapping ray_id -> power at first detector hit (read-only view)."""
        return dict(self._power_by_ray_id)

    def reset(self):
        """Clear counts for the current frame/simulation run."""
        self._seen_ray_ids.clear()
        self._power_by_ray_id.clear()
        self._profile_by_ray_id.clear()

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        rid = getattr(ray, "ray_id", None)
        if rid is not None and rid not in self._seen_ray_ids:
            self._seen_ray_ids.add(rid)
            self._power_by_ray_id[rid] = float(getattr(ray, "power", 0.0))
            # Record a 2D beam cross-section sample for plotting.
            try:
                chord = (self.p2 - self.p1)
                L = chord.length()
                if L > 1e-12:
                    tangent = chord.normalize()
                    center = (self.p1 + self.p2) * 0.5
                    x_px = (hit - center).dot(tangent)  # coordinate along detector segment
                else:
                    x_px = 0.0
                u_px = float(getattr(ray, "u", 0.0))
                p = float(getattr(ray, "power", 0.0))
                self._profile_by_ray_id[int(rid)] = (float(x_px), float(u_px), float(p))
            except Exception:
                pass
        return ray.dir

    @property
    def profile_samples(self):
        """List of (x_px, u_px, power) samples (unique rays only)."""
        return list(self._profile_by_ray_id.values())

    def export_profile_plots(
        self,
        out_dir: str,
        um_per_px: float = 1.0,
        name: str | None = None,
        bins: int = 80,
    ) -> dict[str, str]:
        """Export detector beam profile as a heatmap and 3D surface plot.

        The plot axes are:
          - x: coordinate along detector segment (µm)
          - y: out-of-plane coordinate u (µm)
          - z: accumulated power per bin
        """
        # Lazy imports so the main simulator can run without these optional deps.
        try:
            import numpy as np
            import matplotlib
            matplotlib.use("Agg")  # headless export
            import matplotlib.pyplot as plt
        except Exception:
            return {}

        samples = self.profile_samples
        if not samples:
            return {}

        os.makedirs(out_dir, exist_ok=True)
        label = (name or self.label or "detector").strip().replace(" ", "_")

        xs_px = np.array([s[0] for s in samples], dtype=float)
        us_px = np.array([s[1] for s in samples], dtype=float)
        ws = np.array([s[2] for s in samples], dtype=float)

        xs = xs_px * float(um_per_px)
        ys = us_px * float(um_per_px)

        # Robust range (avoid single outlier exploding the plot)
        def _robust_range(a: np.ndarray):
            if a.size < 4:
                mn, mx = float(np.min(a)), float(np.max(a))
            else:
                mn, mx = np.percentile(a, [1.0, 99.0])
            if abs(mx - mn) < 1e-9:
                mn -= 1.0
                mx += 1.0
            pad = 0.08 * (mx - mn)
            return float(mn - pad), float(mx + pad)

        x_min, x_max = _robust_range(xs)
        y_min, y_max = _robust_range(ys)

        H, xedges, yedges = np.histogram2d(
            xs,
            ys,
            bins=int(max(10, bins)),
            range=[[x_min, x_max], [y_min, y_max]],
            weights=ws,
        )

        # Save grid CSV (optional but useful for reports)
        csv_path = os.path.join(out_dir, f"{label}_intensity_grid.csv")
        np.savetxt(csv_path, H, delimiter=",")

        # Heatmap
        heat_path = os.path.join(out_dir, f"{label}_heatmap.png")
        plt.figure(figsize=(6.5, 5.2))
        plt.imshow(
            H.T,
            origin="lower",
            extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
            aspect="auto",
        )
        plt.xlabel("x along detector (µm)")
        plt.ylabel("out-of-plane u (µm)")
        plt.title(f"Beam profile: {label}")
        plt.colorbar(label="Power (a.u.)")
        plt.tight_layout()
        plt.savefig(heat_path, dpi=180)
        plt.close()

        # 3D surface plot
        surf_path = os.path.join(out_dir, f"{label}_surface.png")
        x_centers = 0.5 * (xedges[:-1] + xedges[1:])
        y_centers = 0.5 * (yedges[:-1] + yedges[1:])
        X, Y = np.meshgrid(x_centers, y_centers, indexing="xy")
        Z = H.T

        fig = plt.figure(figsize=(7.0, 5.5))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_surface(X, Y, Z, rstride=1, cstride=1, linewidth=0, antialiased=True)
        ax.set_xlabel("x along detector (µm)")
        ax.set_ylabel("out-of-plane u (µm)")
        ax.set_zlabel("Intensity (power)")
        ax.set_title(f"Beam profile surface: {label}")
        fig.tight_layout()
        fig.savefig(surf_path, dpi=180)
        plt.close(fig)

        return {"heatmap": heat_path, "surface": surf_path, "csv": csv_path}

    def draw(self, screen):
        pygame.draw.line(screen, DETECTOR_COLOR, self.p1.tuple(), self.p2.tuple(), 4)

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8

    def get_params_str(self):
        return [
            f"Detector: p1=({self.p1.x:.1f}, {self.p1.y:.1f})",
            f"p2=({self.p2.x:.1f}, {self.p2.y:.1f})",
            (f"label={self.label}" if self.label else ""),
            f"count={self.count}, power_sum={self.power_sum:.4f}",
            f"profile_samples={len(self._profile_by_ray_id)}"
        ]
