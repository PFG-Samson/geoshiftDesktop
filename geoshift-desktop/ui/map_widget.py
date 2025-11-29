import io
import os
import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import base64
from engine.logger import logger

class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        # Default: blank screen
        self._show_blank_screen()

    def _show_blank_screen(self):
        """Display a blank white screen with a waiting message."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #ffffff;
                    font-family: Arial, sans-serif;
                }
                .message {
                    text-align: center;
                    color: #95a5a6;
                    font-size: 18px;
                }
            </style>
        </head>
        <body>
            <div class="message">
                <p>Waiting for images...</p>
                <p style="font-size: 14px;">Load Image A and Image B to begin</p>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
        logger.info("Map widget initialized with blank screen")

    def _get_image_url(self, path):
        """Convert local file path to base64 data URI."""
        if not path or not os.path.exists(path):
            logger.warning(f"Image path does not exist: {path}")
            return ""
        try:
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            logger.debug(f"Encoded image: {os.path.basename(path)}")
            return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            logger.error(f"Error encoding image {path}: {e}")
            return ""

    def show_map(self, raster_data, mask_path=None):
        """
        Displays a single raster and optional mask.
        raster_data: dict from reader.load_raster
        mask_path: path to mask image (optional)
        """
        logger.info("show_map called")
        if raster_data:
            bounds = raster_data['bounds']
            center_lat = (bounds.bottom + bounds.top) / 2
            center_lon = (bounds.left + bounds.right) / 2
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
            
            # Add raster overlay
            image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
            
            folium.raster_layers.ImageOverlay(
                image=self._get_image_url(raster_data['preview_path']),
                bounds=image_bounds,
                opacity=1.0,
                name="Imagery"
            ).add_to(m)
            
            if mask_path and os.path.exists(mask_path):
                folium.raster_layers.ImageOverlay(
                    image=self._get_image_url(mask_path),
                    bounds=image_bounds,
                    opacity=0.6,
                    name="Water Mask"
                ).add_to(m)
                
            folium.LayerControl().add_to(m)
            
            data = io.BytesIO()
            m.save(data, close_file=False)
            self.web_view.setHtml(data.getvalue().decode())
            logger.info("Single map view rendered successfully")
        else:
            # Empty map
            m = folium.Map(location=[0, 0], zoom_start=2)
            data = io.BytesIO()
            m.save(data, close_file=False)
            self.web_view.setHtml(data.getvalue().decode())
            logger.info("Empty map rendered")

    def show_comparison(self, raster_a, raster_b, mask_a_path=None, mask_b_path=None):
        """Displays two rasters side-by-side using Folium's DualMap plugin."""
        logger.info("show_comparison called")
        
        if not raster_a or not raster_b:
            logger.warning("Missing raster data for comparison")
            return
        
        try:
            from folium import plugins
            
            # Get bounds from first image
            bounds = raster_a['bounds']
            center_lat = (bounds.bottom + bounds.top) / 2
            center_lon = (bounds.left + bounds.right) / 2
            image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
            
            # Create DualMap with layout parameter
            dual_map = plugins.DualMap(
                location=[center_lat, center_lon],
                zoom_start=10,
                tiles=None,
                layout='horizontal'
            )
            
            # Add base tiles to both maps
            folium.TileLayer('OpenStreetMap', name='Base Map').add_to(dual_map.m1)
            folium.TileLayer('OpenStreetMap', name='Base Map').add_to(dual_map.m2)
            
            # Add Image A to left map (m1)
            folium.raster_layers.ImageOverlay(
                image=self._get_image_url(raster_a['preview_path']),
                bounds=image_bounds,
                opacity=1.0,
                name="Image A"
            ).add_to(dual_map.m1)
            
            if mask_a_path and os.path.exists(mask_a_path):
                folium.raster_layers.ImageOverlay(
                    image=self._get_image_url(mask_a_path),
                    bounds=image_bounds,
                    opacity=0.6,
                    name="Mask A"
                ).add_to(dual_map.m1)
            
            # Add Image B to right map (m2)
            folium.raster_layers.ImageOverlay(
                image=self._get_image_url(raster_b['preview_path']),
                bounds=image_bounds,
                opacity=1.0,
                name="Image B"
            ).add_to(dual_map.m2)
            
            if mask_b_path and os.path.exists(mask_b_path):
                folium.raster_layers.ImageOverlay(
                    image=self._get_image_url(mask_b_path),
                    bounds=image_bounds,
                    opacity=0.6,
                    name="Mask B"
                ).add_to(dual_map.m2)
            
            # Add layer controls
            folium.LayerControl(collapsed=False).add_to(dual_map)
            
            # Render the dual map
            data = io.BytesIO()
            dual_map.save(data, close_file=False)
            self.web_view.setHtml(data.getvalue().decode())
            logger.info("Comparison view rendered successfully with DualMap")
            
        except Exception as e:
            logger.error(f"Error in show_comparison: {e}", exc_info=True)
            # Fallback to single map showing Image B
            logger.info("Falling back to single map view")
            self.show_map(raster_b, mask_b_path)
