class InteractionState:
    def __init__(self):
        # selection
        self.selected = None

        # drag state
        self.dragging = None          # object being edited
        self.drag_mode = None         # 'move' | 'p1' | 'p2' | 'rotate' | ('vertex', idx)
        self.last_mouse = None

        # add-mode state
        self.add_mode = None          # None | 'mirror' | 'lens' | ... | 'media_poly'
        self.start_pos = None         # Vector (for click-drag segment)
        self.current_pos = None       # Vector (preview)
        self.poly_points = []         # list[Vector] for polygon creation

        # media editing
        self.poly_vertex_index = 0    # which vertex is edited in the Properties panel

        # units / overlay state
        self.um_per_px = None
        self.ref_d1_um = None

        # snapping
        self.snap_enabled = True

        # UI input
        self.active_field = None  # a NumericField or similar
