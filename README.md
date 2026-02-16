# Optical Path Simulator — Monte Carlo Ray Tracing (EBO_Monte_Carlo_Simulation)

## About
This project is a **2D optical layout simulator** with a **Monte Carlo ray-tracing** engine for evaluating and optimizing optical setups under parameter tolerances.  
You can build an optical scene in a lightweight **pygame GUI**, save it to JSON, and then run **headless** (no GUI) tools for heavy computation like beam-profile export, Monte Carlo trials, and convergence studies.

## What you can do
- Build and edit an optical layout (sources, mirrors, lenses, interfaces, detector) in the GUI
- Trace rays through the scene and measure power on detectors (e.g., coupling / insertion loss style metrics)
- Run **Monte Carlo trials** by sampling parameters from Gaussian distributions (nominal + sigma)
- Export **beam profiles** (heatmap + 3D surface + CSV grid) for detectors
- Run a **convergence study** to pick a stable number of rays vs. runtime

## Tech stack
- Python 3.10+
- `pygame` (GUI + visualization)
- `numpy` (math)
- `matplotlib` (plots for headless exports)

## Project layout
- `main.py` — GUI application (build/edit scenes, visualize rays)
- `reference_layout.json` — example scene
- `components/` — optical components (mirrors, lenses, detector, sources, interfaces, etc.)
- `core/` — math primitives (vectors, transforms, rays)
- `simulation/` — tracer + Monte Carlo + sweep utilities
- `tools/` — headless scripts (beam profile, Monte Carlo, convergence)
- `exports/` — output folder (auto-created by tools)

## Installation
Create a virtual environment and install dependencies:

Windows (PowerShell):
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install pygame numpy matplotlib

Linux/Mac:
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pygame numpy matplotlib

## Run the GUI
From the project root:

python main.py

In the GUI you can build your layout and **save the scene to JSON** (e.g., using the Scene → Save option).  
You can also start from the included example: `reference_layout.json`.

---

# Headless tools (no pygame window)

These scripts let you run heavy computations without freezing the GUI.  
All commands below assume you run them from the project root.

## 1) Beam profile export (heatmap + 3D surface + CSV)
1. Build your layout in the GUI (or use `reference_layout.json`)
2. Save the scene to JSON
3. Run:

python tools/run_beam_profile.py --scene reference_layout.json --rays 50000 --seed 12345

Outputs are written to:
exports/headless_profiles/<timestamp>/

You’ll typically get files like:
- Detector*_heatmap.png
- Detector*_surface.png
- Detector*_grid.csv

## 2) Monte Carlo run (with progress prints)
Runs multiple trials; for each trial the tool samples parameters and re-runs ray tracing.

python tools/run_monte_carlo.py --scene reference_layout.json --trials 200 --rays 50000 --seed 12345 --sigma-scale 1

Outputs are written to:
exports/

Useful flags:
- `--sigma-scale` : scales all sigmas (0 = nominal only)
- `--trial-progress-every` : print summary every N trials
- `--ray-progress-every` : print ray progress inside a trial

## 3) Convergence study (N_rays → std(IL))
Helps answer:
- “What is the minimal number of rays so IL is stable within ~1 dB?”
- “How does runtime grow with ray count?”

Nominal-only (no perturbations): `--sigma-scale 0`

python tools/run_convergence.py --scene reference_layout.json --rays-list 500,1000,2000,5000,10000,20000,50000 --trials 30 --seed 12345 --sigma-scale 0

Outputs:
exports/convergence/<timestamp>/
- convergence.csv
- rays_vs_stdIL.png
- rays_vs_time.png

---

## Notes / Tips
- If you don’t see plots in headless mode, make sure `numpy` and `matplotlib` are installed.
- For “clean runs” you may want to remove previous outputs in `exports/` (optional).
- For reproducible experiments, set `--seed`.
