WIDTH, HEIGHT = 1200, 620
BG = (15, 23, 42)
RAY_COLOR = (255, 209, 102)
RAY_WIDTH = 2

# Elements
MIRROR_COLOR = (56, 189, 248)
LENSED_MIRROR_COLOR = (14, 165, 233)  # slightly darker than MIRROR_COLOR
LENS_COLOR = (56, 0, 248)
DETECTOR_COLOR = (239, 68, 68)
BEAM_COLOR = (167, 139, 250)

GRID_COLOR = (148, 163, 184)
EPS = 1e-4
MAX_BOUNCES = 10

# --- UI ---
# Top bar keeps the title + quick hints.
UI_BAR_H = 84
UI_BG = (243, 244, 246)

# Left sidebar holds the expandable tool panels.
SIDEBAR_W = 300
SIDEBAR_BG = (241, 245, 249)
SIDEBAR_BORDER = (203, 213, 225)
SIDEBAR_PAD = 10
BTN_BG = (255, 255, 255)
BTN_BORDER = (203, 213, 225)
TEXT_COLOR = (0, 0, 0)

# UI sizing
FONT_SIZE = 20
FONT_SMALL_SIZE = 16
OVERLAY_LINE_STEP = 24

# Sidebar layout
GROUP_HEADER_H = 36
GROUP_BUTTON_H = 32
GROUP_PAD = 10
GROUP_GAP = 8

# --- Units (pixels -> micrometers) ---
# Start with 1.0 µm/px. Press "C" in the main app to calibrate.
UM_PER_PX_DEFAULT = 1.0
REF_D1_UM_DEFAULT = 615.0
OVERLAY_MAX_HITS = 30

# --- LensedMirror interaction ---
BULGE_WHEEL_STEP = 5.0
BULGE_WHEEL_MAX_ABS = 400.0

# --- Beam defaults ---
BEAM_DEFAULT_SPREAD_DEG = 12.0
BEAM_DEFAULT_POS_SPACING_PX = 10.0
BEAM_DEFAULT_ANGLE_SAMPLES = 5

# --- Medium defaults ---
ALPHA_PER_UM_DEFAULT = 0.0  # absorption coefficient, 1/µm
