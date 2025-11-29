import rasterio
from rasterio.plot import reshape_as_image
from rasterio.warp import transform_bounds
import numpy as np
from PIL import Image
import os
from engine.logger import logger

def load_raster(path, max_size=1024):
    """
    Loads a raster file metadata and generates a downsampled preview.
    Does NOT load the full array into memory.
    """
    try:
        with rasterio.open(path) as src:
            profile = src.profile
            transform = src.transform
            crs = src.crs
            bounds = src.bounds
            width = src.width
            height = src.height
            count = src.count
            
            logger.info(f"Loading raster: {os.path.basename(path)}")
            logger.info(f"Original CRS: {crs}")
            logger.info(f"Original bounds: {bounds}")
            
            # Reproject bounds to WGS84 (EPSG:4326) for Folium
            if crs and crs != 'EPSG:4326':
                try:
                    wgs84_bounds = transform_bounds(crs, 'EPSG:4326', *bounds)
                    logger.info(f"Reprojected bounds to WGS84: {wgs84_bounds}")
                    # Create a BoundingBox-like object
                    from collections import namedtuple
                    BBox = namedtuple('BBox', ['left', 'bottom', 'right', 'top'])
                    bounds_wgs84 = BBox(*wgs84_bounds)
                except Exception as e:
                    logger.warning(f"Could not reproject bounds: {e}. Using original bounds.")
                    bounds_wgs84 = bounds
            else:
                logger.info("CRS is already WGS84 or undefined")
                bounds_wgs84 = bounds
            
            # Calculate downsample factor
            scale = max(1, max(width, height) / max_size)
            
            # Read downsampled data for preview
            # out_shape = (count, int(height / scale), int(width / scale))
            out_shape = (count, int(height // scale), int(width // scale))
            
            if count >= 3:
                preview_data = src.read([1, 2, 3], out_shape=(3, out_shape[1], out_shape[2]))
            else:
                preview_data = src.read(1, out_shape=(1, out_shape[1], out_shape[2]))
            
            # Normalize for preview
            preview_data = preview_data.astype(float)
            p_min = np.nanmin(preview_data)
            p_max = np.nanmax(preview_data)
            
            if p_max > p_min:
                preview_data = ((preview_data - p_min) / (p_max - p_min) * 255).astype(np.uint8)
            else:
                preview_data = np.zeros_like(preview_data, dtype=np.uint8)
            
            if count >= 3:
                img = reshape_as_image(preview_data)
                image = Image.fromarray(img)
            else:
                image = Image.fromarray(preview_data[0], mode='L')
            
            # Save preview
            preview_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'previews')
            os.makedirs(preview_dir, exist_ok=True)
            preview_filename = f"preview_{os.path.basename(path)}.png"
            preview_path = os.path.join(preview_dir, preview_filename)
            image.save(preview_path)
            logger.info(f"Saved preview to: {preview_path}")
            
            return {
                "path": path,
                "transform": transform,
                "crs": crs,
                "bounds": bounds_wgs84,  # Use WGS84 bounds for Folium
                "width": width,
                "height": height,
                "count": count,
                "meta": profile,
                "preview_path": preview_path
            }
    except Exception as e:
        logger.error(f"Error loading raster: {e}", exc_info=True)
        return None
