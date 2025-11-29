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
- **Interactive Comparison**: Side-by-side dual map view with synchronized panning/zooming
- **Symbology Panel**: Adjust image visualization (Opacity, Brightness, Contrast)
- **Change Visualization**: Color-coded change overlays with toggle control
- **Export Reports**: HTML reports with before/after comparisons
- **Comprehensive Logging**: File and console logging for debugging
- **Clean UX**: Blank initial state with clear waiting indicators

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
1. **Initial State**: Application starts with a blank screen showing "Waiting for images..."
2. Click **"Load Image A (Before)"** to load the first image
3. Click **"Load Image B (After)"** to load the second image
4. *(Optional)* Adjust image visualization using the **Symbology Panel**:
   - Opacity (0-100%)
   - Brightness (-100% to +100%)
   - Contrast (0-200%)
5. Select analysis type from the dropdown
6. Click **"Run Analysis"**
7. View change overlay on the interactive comparison slider
8. Toggle change overlay visibility with **"Toggle Change Overlay"**
9. Export HTML report with **"Export Report"**

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
├── engine/          # Core processing logic (formerly core/)
│   ├── logger.py           # Centralized logging system
│   ├── reader.py           # Raster file loading with coordinate reprojection
│   ├── analysis_change.py  # Change detection algorithms
│   ├── change_tools.py     # Change visualization utilities
│   ├── exporter.py         # Report generation
│   └── models_manager.py   # AI model management
├── ui/              # User interface components
│   ├── main_window.py      # Main application window
│   ├── map_widget.py       # Folium DualMap integration
│   ├── symbology_panel.py  # Image adjustment controls
│   └── dialogs/            # File dialogs
├── models/          # AI/ML models
├── assets/          # Application assets
├── logs/            # Application logs (auto-generated)
└── main.py          # Application entry point
```

## Logging
The application maintains detailed logs for debugging:
- **Location**: `logs/geoshift_YYYYMMDD.log`
- **Levels**: DEBUG (file), INFO (console)
- **Contents**: Image loading, coordinate reprojection, analysis execution, errors

Example log output:
```
2025-11-29 12:51:58 - geoshift - INFO - Loading Image A: example.tif
2025-11-29 12:51:58 - geoshift - INFO - Original CRS: EPSG:32633
2025-11-29 12:51:58 - geoshift - INFO - Reprojected bounds to WGS84: (6.5, 51.2, 6.6, 51.3)
```

## Technical Details
- **Framework**: PyQt5
- **Geospatial**: Rasterio, GDAL (with coordinate reprojection)
- **Image Processing**: OpenCV, NumPy
- **Visualization**: Folium DualMap, Leaflet
- **Logging**: Python logging module with file and console handlers
- **AI/ML**: PyTorch (models bundled)

## Packaging
To build the executable:
```bash
pyinstaller --noconfirm --onefile --add-data "models;models" --add-data "assets;assets" --add-data "ui/js;ui/js" main.py
```

## Model Information
Current implementation uses placeholder algorithms. For production:
1. Train models on labeled datasets
2. Export to `.pt` format
3. Place in `models/` directory
4. Update `model_config.json`

## System Requirements
- Python 3.10+
- 8GB RAM minimum (16GB recommended for large files)
- Windows/Linux/macOS
