# Geoshift Desktop - Change Detection Platform

Geoshift Desktop is an offline geospatial change detection platform. Load two images (before/after), run AI-powered analysis, and detect changes like deforestation, water expansion, new structures, and disaster damage.

## Features
- **Multi-Purpose Detection**: 5 analysis types
  - Land-use Change
  - Deforestation
  - Water Body Expansion/Retraction
  - New Structures
  - Disaster Damage Assessment
- **Offline Processing**: All analysis runs locally, no internet required
- **Large File Support**: Handles GeoTIFFs and regular photos up to 2GB+
- **GeoTIFF Support**: Automatic coordinate system reprojection to WGS84
- **Professional GIS Viewer**:
  - **Layer Management**: Toggle visibility, remove layers, and zoom to extent via the Layers Panel.
  - **Side-by-Side Comparison**: Interactive slider to compare "Before" and "After" images.
  - **Symbology Control**: Adjust opacity for each layer.
  - **Top Toolbar**: Quick access to Load, Swap, and Clear functions.
  - **Status Bar**: Real-time metadata display (CRS, dimensions).
- **Change Visualization**: Color-coded change overlays with toggle control
- **Export Reports**: HTML reports with before/after comparisons
- **Comprehensive Logging**: File and console logging for debugging

## Installation
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Navigate to the project directory:
```bash
cd geoshift-desktop
```

Run the application:
```bash
python main.py
```

### Workflow
1. **Load Images**:
   - Click **"Load A"** (or use the sidebar) to load the "Before" image.
   - Click **"Load B"** to load the "After" image.
   - The map will automatically zoom to the image extent.
2. **Compare Images**:
   - Use the **Side-by-Side Slider** in the center of the map to swipe between images.
   - Use the **Layers Panel** (right sidebar) to toggle visibility or remove layers.
   - Use the **Swap** button in the top toolbar to switch Image A and B.
3. **Adjust Visualization**:
   - Select a layer in the Layers Panel.
   - Use the **Symbology Panel** (left sidebar) to adjust **Opacity**.
4. **Run Analysis**:
   - Select an analysis type from the dropdown (Left Sidebar).
   - Click **"Run Analysis"**.
5. **View Results**:
   - The change mask will appear as a new layer.
   - Toggle its visibility using the checkbox in the Layers Panel or the "Toggle Overlay" button.
6. **Export**:
   - Click **"Export Report"** to save an HTML summary.

## Supported Formats
- GeoTIFF (.tif, .tiff)
- JPEG (.jpg, .jpeg)
- PNG (.png)

## Analysis Types

### Land-use Change
Detects general changes in land cover and usage patterns.

### Deforestation
Identifies areas where forest cover has been lost.

### Water Change
Detects expansion or retraction of water bodies.

### New Structures
Identifies newly constructed buildings and infrastructure.

### Disaster Damage
Assesses damage from natural disasters by comparing before/after imagery.

## Project Structure
```
geoshift-desktop/
├── engine/          # Core processing logic
│   ├── logger.py           # Centralized logging system
│   ├── reader.py           # Raster loading & PNG conversion for Leaflet
│   ├── analysis_change.py  # Change detection algorithms
│   ├── change_tools.py     # Change visualization utilities
│   ├── exporter.py         # Report generation
│   └── models_manager.py   # AI model management
├── ui/              # User interface components
│   ├── main_window.py      # Main application window & layout
│   ├── map_widget.py       # Map engine (Folium + Leaflet + SideBySide)
│   ├── layer_panel.py      # Layer management widget
│   ├── symbology_panel.py  # Opacity/visualization controls
│   └── dialogs/            # File dialogs
├── models/          # AI/ML models
├── assets/          # Application assets (previews, icons)
├── logs/            # Application logs
└── main.py          # Application entry point
```

## Logging
The application maintains detailed logs for debugging:
- **Location**: `logs/geoshift_YYYYMMDD.log`
- **Levels**: DEBUG (file), INFO (console)
- **Contents**: Image loading, coordinate reprojection, analysis execution, errors

## Technical Details
- **Framework**: PyQt5
- **Geospatial**: Rasterio, GDAL (reprojection to WGS84)
- **Map Engine**: Folium with Leaflet.js and `leaflet-side-by-side` plugin
- **Image Processing**: OpenCV, NumPy
- **Logging**: Python logging module
- **AI/ML**: PyTorch (models bundled)

## Packaging
To build the executable:
```bash
pyinstaller --noconfirm --onefile --add-data "models;models" --add-data "assets;assets" --add-data "ui/js;ui/js" main.py
```

## System Requirements
- Python 3.10+
- 8GB RAM minimum (16GB recommended for large files)
- Windows/Linux/macOS
