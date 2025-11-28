class AppState:
    def __init__(self):
        # Image state (always comparison mode)
        self.raster_a = None  # Before image
        self.raster_b = None  # After image
        
        # Analysis state
        self.selected_analysis_type = 'landuse'  # Default
        self.change_mask = None
        self.change_results = None
        
        # UI State
        self.change_visible = True

    def reset(self):
        """Reset all state."""
        self.raster_a = None
        self.raster_b = None
        self.change_mask = None
        self.change_results = None
        self.change_visible = True
    
    def has_both_images(self) -> bool:
        """Check if both images are loaded."""
        return self.raster_a is not None and self.raster_b is not None
