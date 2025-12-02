# Installation Instructions for PyQtGraph Dependencies

## Required Packages
- `pyqtgraph` >= 0.13.0
- `PyOpenGL` >= 3.1.0  
- `PyOpenGL-accelerate` >= 3.1.0

## Installation Steps

### Option 1: Using Conda (Recommended)

**Run PowerShell as Administrator**, then:

```bash
cd "c:\Users\Samson Adeyomoye\Desktop\Desktop_Geoshift\geoshift-desktop"
conda install -c conda-forge pyqtgraph pyopengl -y
```

### Option 2: Using pip

**Run PowerShell as Administrator**, then:

```bash
cd "c:\Users\Samson Adeyomoye\Desktop\Desktop_Geoshift\geoshift-desktop"
pip install pyqtgraph PyOpenGL PyOpenGL-accelerate
```

## Verification

After installation, test with:

```bash
python -c "import pyqtgraph as pg; print('PyQtGraph version:', pg.__version__)"
python -c "import OpenGL; print('PyOpenGL installed successfully')"
```

## Troubleshooting

If you get "Access Denied" errors:
1. Right-click PowerShell
2. Select "Run as Administrator"
3. Try the installation command again

## Next Steps

Once installed, restart the application to use the new PyQtGraph-based map widget.
