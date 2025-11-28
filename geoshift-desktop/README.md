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
- **Interactive Comparison**: Side-by-side slider view
- **Change Visualization**: Color-coded change overlays
- **Export Reports**: HTML reports with before/after comparisons

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
1. Click "Load Image A (Before)" to load the first image
2. Click "Load Image B (After)" to load the second image
3. Select analysis type from the dropdown
4. Click "Run Analysis"
5. View change overlay on the comparison slider
6. Export report

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

## Technical Details
- **Framework**: PyQt5
- **Geospatial**: Rasterio, GDAL
- **Image Processing**: OpenCV, NumPy
- **Visualization**: Folium, Leaflet
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
