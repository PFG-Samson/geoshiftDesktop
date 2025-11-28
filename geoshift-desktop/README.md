# Geoshift Desktop

Geoshift Desktop is an offline geospatial intelligence tool designed for water body detection and analysis. It allows users to load large imagery (GeoTIFF, JPG, PNG), perform water body detection using NDWI or CNN models, and export detailed reports.

## Features
- **Raster Loading**: Supports GeoTIFF, JPEG, PNG.
- **Map Display**: Interactive map using Folium and PyQtWebEngine.
- **Water Analysis**: NDWI (Normalized Difference Water Index) calculation and optional CNN-based segmentation.
- **Mask Visualization**: Overlay detected water bodies on the map.
- **Area Calculation**: Calculate water area in hectares and percentage coverage.
- **Reporting**: Export results to HTML/PDF.
- **Imagery Comparison**: Compare two images side-by-side with a slider.

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

## Packaging
To build the executable:
```bash
pyinstaller --noconfirm --onefile --add-data "models;models" --add-data "assets;assets" --add-data "ui/js;ui/js" main.py
```

## Imagery Comparison Slider
Geoshift Desktop supports comparing two images using a draggable slider.
Load Image A and Image B, then activate Compare Mode. The viewer will
display both rasters side-by-side with a vertical handle for interactive comparison.
