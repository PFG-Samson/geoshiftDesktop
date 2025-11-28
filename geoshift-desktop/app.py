class AppState:
    def __init__(self):
        # Single mode state
        self.raster = None
        self.mask = None
        self.ndwi = None
        self.results = None
        self.raster_path = None
        
        # Comparison mode state
        self.raster_a = None
        self.raster_b = None
        self.mask_a = None
        self.mask_b = None
        self.results_a = None
        self.results_b = None
        self.compare_mode = False
        self.active_raster = None # 'A' or 'B' or None
        
        # UI State
        self.mask_visible = True

    def reset_single_mode(self):
        self.raster = None
        self.mask = None
        self.ndwi = None
        self.results = None
        self.raster_path = None
        self.mask_visible = True

    def reset_compare_mode(self):
        self.raster_a = None
        self.raster_b = None
        self.mask_a = None
        self.mask_b = None
        self.results_a = None
        self.results_b = None
        self.compare_mode = False
