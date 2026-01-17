class InteractionState:
    def __init__(self):
        # selection
        self.selected = None

        # drag state
        self.dragging = None          # object being edited
        self.drag_mode = None         # 'move' | 'p1' | 'p2' | 'rotate'
        self.last_mouse = None

        # add-mode state (click-drag to create a new segment)
        self.add_mode = None          # None | 'mirror' | 'lens' | ...
        self.start_pos = None         # Vector
        self.current_pos = None       # Vector

        # units / overlay state
        self.um_per_px = None
        self.ref_d1_um = None
