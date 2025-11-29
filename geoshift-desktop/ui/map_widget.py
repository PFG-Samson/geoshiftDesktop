import io
import os
import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import base64

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

    def _get_image_url(self, path):
        """Convert local file path to base64 data URI."""
        if not path or not os.path.exists(path):
            return ""
        try:
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            print(f"Error encoding image {path}: {e}")
            return ""

    def show_map(self, raster_data, mask_path=None):
        """
        Displays a single raster and optional mask.
        raster_data: dict from reader.load_raster
        mask_path: path to mask image (optional)
        """
        if raster_data:
            bounds = raster_data['bounds']
            # Folium expects [[lat_min, lon_min], [lat_max, lon_max]]
            # Rasterio bounds: (left, bottom, right, top) -> (min_x, min_y, max_x, max_y)
            # If CRS is projected, this might need reprojection to lat/lon (EPSG:4326).
            # For MVP, assuming input might be projected, but Folium needs 4326.
            # If we don't reproject, the map tiles won't match. 
            # However, for simple image overlay, we can just center on the image bounds 
            # if we disable base tiles or if the image is already 4326.
            # Let's assume we just want to see the image.
            
            # Calculate center
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
        else:
            # Empty map
            m = folium.Map(location=[0, 0], zoom_start=2)
            data = io.BytesIO()
            m.save(data, close_file=False)
            self.web_view.setHtml(data.getvalue().decode())

    def show_comparison(self, raster_a, raster_b, mask_a_path=None, mask_b_path=None):
        """Displays two rasters with a comparison slider, optionally with masks."""
        if not raster_a or not raster_b:
            return
        
        # Use Simple CRS (pixels) to avoid projection issues
        height = raster_a['height']
        width = raster_a['width']
        image_bounds = [[0, 0], [height, width]]
        
        m = folium.Map(location=[height/2, width/2], zoom_start=0, crs='Simple', tiles=None)
        
        # Fit bounds to ensure images are visible
        m.fit_bounds(image_bounds)
        
        # Left Side (Image A + Mask A)
        group_a = folium.FeatureGroup(name="Group A")
        folium.raster_layers.ImageOverlay(
            image=self._get_image_url(raster_a['preview_path']),
            bounds=image_bounds,
            name="Image A"
        ).add_to(group_a)
        
        if mask_a_path and os.path.exists(mask_a_path):
            folium.raster_layers.ImageOverlay(
                image=self._get_image_url(mask_a_path),
                bounds=image_bounds,
                opacity=0.6,
                name="Mask A"
            ).add_to(group_a)
            
        group_a.add_to(m)

        # Right Side (Image B + Mask B)
        group_b = folium.FeatureGroup(name="Group B")
        folium.raster_layers.ImageOverlay(
            image=self._get_image_url(raster_b['preview_path']),
            bounds=image_bounds,
            name="Image B"
        ).add_to(group_b)
        
        if mask_b_path and os.path.exists(mask_b_path):
            folium.raster_layers.ImageOverlay(
                image=self._get_image_url(mask_b_path),
                bounds=image_bounds,
                opacity=0.6,
                name="Mask B"
            ).add_to(group_b)
            
        group_b.add_to(m)

        # Inject Side-by-Side JS/CSS
        # We use the bundled files in ui/js
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            js_path = os.path.join(base_dir, 'ui', 'js', 'leaflet-side-by-side.min.js')
            css_path = os.path.join(base_dir, 'ui', 'js', 'leaflet-side-by-side.css')

            if not os.path.exists(js_path):
                print(f"Error: JS file not found at {js_path}")
                return
            if not os.path.exists(css_path):
                print(f"Error: CSS file not found at {css_path}")
                return

            with open(js_path, 'r') as f:
                js_content = f.read()
            with open(css_path, 'r') as f:
                css_content = f.read()
                
            m.get_root().header.add_child(folium.Element(f'<style>{css_content}</style>'))
            m.get_root().header.add_child(folium.Element(f'<script>{js_content}</script>'))
            
            from branca.element import MacroElement
            from jinja2 import Template
            
            class SideBySide(MacroElement):
                def __init__(self, layer_left, layer_right):
                    super(SideBySide, self).__init__()
                    self._template = Template("""
                        {% macro script(this, kwargs) %}
                        var sideBySide = L.control.sideBySide(
                            {{ this.layer_left.get_name() }},
                            {{ this.layer_right.get_name() }}
                        ).addTo({{ this._parent.get_name() }});
                        {% endmacro %}
                    """)
                    self.layer_left = layer_left
                    self.layer_right = layer_right

            m.add_child(SideBySide(group_a, group_b))

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error injecting comparison slider: {e}")

        data = io.BytesIO()
        m.save(data, close_file=False)
        self.web_view.setHtml(data.getvalue().decode())
