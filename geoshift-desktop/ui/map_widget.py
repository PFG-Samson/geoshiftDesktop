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
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #2c3e50;
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                    border: 2px dashed #bdc3c7;
                    max-width: 400px;
                    width: 100%;
                }
                .icon {
                    font-size: 48px;
                    color: #3498db;
                    margin-bottom: 20px;
                }
                h1 {
                    font-size: 24px;
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                }
                p {
                    font-size: 14px;
                    color: #7f8c8d;
                    margin: 0;
                    line-height: 1.5;
                }
                .steps {
                    margin-top: 20px;
                    text-align: left;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                }
                .step {
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;
                    font-size: 13px;
                }
                .step-num {
                    background: #3498db;
                    color: white;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 11px;
                    margin-right: 10px;
                    flex-shrink: 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🗺️</div>
                <h1>Start Analysis</h1>
                <p>Load your before and after images to begin change detection.</p>
                
                <div class="steps">
                    <div class="step">
                        <div class="step-num">1</div>
                        <div>Load <b>Image A</b> (Before)</div>
                    </div>
                    <div class="step">
                        <div class="step-num">2</div>
                        <div>Load <b>Image B</b> (After)</div>
                    </div>
                    <div class="step">
                        <div class="step-num">3</div>
                        <div>Select <b>Analysis Type</b></div>
                    </div>
                </div>
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
