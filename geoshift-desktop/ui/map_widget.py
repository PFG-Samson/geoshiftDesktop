import io
import os
import folium
from folium import plugins
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

        # Initialize layer storage and map defaults
        self.layers = {}  # key: layer name, value: dict with raster_data, mask_path, visible, opacity, bounds
        self.base_location = [0, 0]
        self.base_zoom = 2
        self.comparison_mode = False  # If True, enables SideBySide slider

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
                    <div class="step"><div class="step-num">1</div><div>Load <b>Image A</b> (Before)</div></div>
                    <div class="step"><div class="step-num">2</div><div>Load <b>Image B</b> (After)</div></div>
                    <div class="step"><div class="step-num">3</div><div>Select <b>Analysis Type</b></div></div>
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

    # Layer management methods
    def add_image_layer(self, name, raster_data, mask_path=None, opacity=1.0, visible=True, render=True):
        """Add an image (and optional mask) as a layer and re‑render the map."""
        bounds = raster_data['bounds']
        layer_info = {
            'raster_data': raster_data,
            'mask_path': mask_path,
            'opacity': opacity,
            'visible': visible,
            'bounds': bounds
        }
        self.layers[name] = layer_info
        if render:
            self._render_map()

    def remove_layer(self, name):
        """Remove a layer by name and re‑render the map."""
        if name in self.layers:
            del self.layers[name]
            self._render_map()
        else:
            logger.warning(f"Attempted to remove non‑existent layer: {name}")

    def clear_all_layers(self, show_blank=True):
        """Remove all image layers and optionally reset to blank map."""
        self.layers.clear()
        if show_blank:
            self._show_blank_screen()

    def toggle_layer_visibility(self, name, visible):
        """Toggle visibility of a layer and re‑render the map."""
        if name in self.layers:
            self.layers[name]['visible'] = visible
            self._render_map()
        else:
            logger.warning(f"Layer not found for visibility toggle: {name}")

    def zoom_to_layer(self, name):
        """Zoom the map view to the bounds of the specified layer."""
        if name in self.layers:
            bounds = self.layers[name]['bounds']
            center_lat = (bounds.bottom + bounds.top) / 2
            center_lon = (bounds.left + bounds.right) / 2
            js = f"map.setView([{center_lat}, {center_lon}], 12);"
            self.web_view.page().runJavaScript(js)
        else:
            logger.warning(f"Cannot zoom to unknown layer: {name}")

    def _render_map(self):
        """Render the Folium map with current base layer and all active image layers."""
        if self.layers:
            first = next((l for l in self.layers.values() if l['visible']), None)
            if first:
                bounds = first['bounds']
                center_lat = (bounds.bottom + bounds.top) / 2
                center_lon = (bounds.left + bounds.right) / 2
                zoom = 10
            else:
                center_lat, center_lon, zoom = self.base_location[0], self.base_location[1], self.base_zoom
        else:
            center_lat, center_lon, zoom = self.base_location[0], self.base_location[1], self.base_zoom

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
        folium.TileLayer('OpenStreetMap', name='Base Map').add_to(m)
        # Store layer objects for SideBySide
        layer_objects = {}
        for name, info in self.layers.items():
            if not info['visible']:
                continue
            raster = info['raster_data']
            bounds = [[raster['bounds'].bottom, raster['bounds'].left], [raster['bounds'].top, raster['bounds'].right]]
            
            layer = folium.raster_layers.ImageOverlay(
                image=self._get_image_url(raster['preview_path']),
                bounds=bounds,
                opacity=info['opacity'],
                name=name
            )
            layer.add_to(m)
            layer_objects[name] = layer
            
            if info['mask_path'] and os.path.exists(info['mask_path']):
                folium.raster_layers.ImageOverlay(
                    image=self._get_image_url(info['mask_path']),
                    bounds=bounds,
                    opacity=0.6,
                    name=f"{name} Mask"
                ).add_to(m)
        
        # Add SideBySide slider if in comparison mode and we have exactly 2 image layers
        if self.comparison_mode and len(layer_objects) >= 2:
            # Assume first two keys are the ones to compare (usually Image A and Image B)
            keys = list(layer_objects.keys())
            logger.info(f"Comparison mode active. Layer keys: {keys}")
            # Try to find 'Image A' and 'Image B' specifically
            left_layer = layer_objects.get('Image A') or layer_objects[keys[0]]
            right_layer = layer_objects.get('Image B') or layer_objects[keys[1]]
            
            if left_layer and right_layer:
                logger.info("Adding SideBySide slider plugin")
                plugins.SideBySideLayers(layer_left=left_layer, layer_right=right_layer).add_to(m)
            else:
                logger.warning(f"Could not create slider: left_layer={left_layer}, right_layer={right_layer}")
        else:
            logger.info(f"Slider not added: comparison_mode={self.comparison_mode}, layer_count={len(layer_objects)}")


        folium.LayerControl(collapsed=False).add_to(m)
        data = io.BytesIO()
        m.save(data, close_file=False)
        html_content = data.getvalue().decode()
        
        # Inject Polyfill for ImageOverlay.getContainer (required for SideBySide plugin with newer Leaflet)
        polyfill = """
        <script>
            L.ImageOverlay.prototype.getContainer = function() { return this.getElement(); };
        </script>
        """
        
        # Add custom CSS to make the slider more visible
        slider_css = """
        <style>
            /* Make the comparison slider more visible */
            .leaflet-sbs-divider {
                background-color: white !important;
                width: 4px !important;
                box-shadow: 0 0 10px rgba(0,0,0,0.5) !important;
                cursor: ew-resize !important;
            }
            .leaflet-sbs-range {
                position: absolute;
                top: 50%;
                width: 100%;
                z-index: 999;
            }
            /* Add a handle/grip to the slider */
            .leaflet-sbs-divider:before {
                content: '⬌';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 10px;
                border-radius: 50%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                font-size: 20px;
                color: #3498db;
            }
        </style>
        """
        
        # Insert before closing head tag
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{polyfill}\n{slider_css}\n</head>")
        else:
            # Fallback: insert at start of body
            html_content = html_content.replace("<body>", f"<body>\n{polyfill}")
            
        self.web_view.setHtml(html_content)
        logger.info("Map rendered with current layers")

    def show_map(self, raster_data, mask_path=None):
        """Display a single raster (and optional mask) using layer management."""
        logger.info("show_map called")
        if raster_data:
            layer_name = raster_data.get('name', 'Image')
            self.add_image_layer(layer_name, raster_data, mask_path)
        else:
            self._show_blank_screen()

    def show_comparison(self, raster_a, raster_b, mask_a_path=None, mask_b_path=None):
        """Display two rasters side‑by‑side using Folium's SideBySideLayers plugin.
        
        This method:
        1. Validates input rasters
        2. Clears existing layers
        3. Adds both rasters as separate image layers
        4. Sets comparison_mode flag to True
        5. Renders the map with SideBySideLayers plugin (handled in _render_map)
        
        The interactive slider is automatically added by _render_map when comparison_mode is True.
        """
        logger.info("show_comparison called")
        if not raster_a or not raster_b:
            logger.warning("Missing raster data for comparison")
            return
        self.clear_all_layers(show_blank=False)
        name_a = raster_a.get('name', 'Image A')
        name_b = raster_b.get('name', 'Image B')
        # Add layers but don't render yet
        self.add_image_layer(name_a, raster_a, mask_a_path, visible=True, render=False)
        self.add_image_layer(name_b, raster_b, mask_b_path, visible=True, render=False)
        
        self.comparison_mode = True
        self._render_map()
