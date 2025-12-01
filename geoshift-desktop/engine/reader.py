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
            
            # Get nodata value
            nodata = src.nodata
            logger.info(f"Nodata value: {nodata}")
            
            # Calculate downsample factor
            scale = max(1, max(width, height) / max_size)
            
            # Read downsampled data for preview
            out_shape = (count, int(height // scale), int(width // scale))
            
            if count >= 3:
                preview_data = src.read([1, 2, 3], out_shape=(3, out_shape[1], out_shape[2]))
            else:
                preview_data = src.read(1, out_shape=(1, out_shape[1], out_shape[2]))
            
            # Create valid data mask
            if nodata is not None:
                valid_mask = preview_data != nodata
            else:
                # If no nodata defined, assume 0 is nodata for satellite imagery if min is 0
                if np.nanmin(preview_data) == 0:
                    valid_mask = preview_data != 0
                    logger.info("No nodata value defined, assuming 0 is nodata")
                else:
                    valid_mask = np.ones_like(preview_data, dtype=bool)
            
            # Normalize for preview using percentile-based contrast stretching
            preview_data = preview_data.astype(float)
            
            # Use valid pixels for percentile calculation
            valid_pixels = preview_data[valid_mask]
            
            if valid_pixels.size > 0:
                p_low = np.nanpercentile(valid_pixels, 2)
                p_high = np.nanpercentile(valid_pixels, 98)
                
                logger.info(f"Preview data range: min={np.nanmin(preview_data):.2f}, max={np.nanmax(preview_data):.2f}")
                logger.info(f"Contrast stretch (valid pixels): 2nd percentile={p_low:.2f}, 98th percentile={p_high:.2f}")
                
                if p_high > p_low:
                    # Clip to percentile range and normalize to 0-255
                    preview_data = np.clip(preview_data, p_low, p_high)
                    preview_data = ((preview_data - p_low) / (p_high - p_low) * 255).astype(np.uint8)
                    
                    # Check if image is still very dark (mean < 50), apply additional enhancement
                    mean_val = np.mean(preview_data[valid_mask])
                    logger.info(f"Preview mean value after stretch: {mean_val:.2f}")
                    
                    if mean_val < 50:
                        logger.info("Image appears dark, applying gamma correction")
                        gamma = 1.5
                        preview_data = np.power(preview_data / 255.0, 1/gamma) * 255
                        preview_data = preview_data.astype(np.uint8)
                else:
                    logger.warning("No contrast in image data, using zeros")
                    preview_data = np.zeros_like(preview_data, dtype=np.uint8)
            else:
                logger.warning("No valid pixels found")
                preview_data = np.zeros_like(preview_data, dtype=np.uint8)
            
            # Create alpha channel from valid mask
            # For RGB, pixel is valid if all bands are valid (or any? usually all)
            # Let's say valid if ANY band is valid (conservative) or ALL?
            # Usually nodata is set on all bands.
            if count >= 3:
                # Collapse mask to 2D: valid if all channels are valid
                alpha_mask = np.all(valid_mask, axis=0).astype(np.uint8) * 255
                
                img = reshape_as_image(preview_data)
                img_rgb = Image.fromarray(img, mode='RGB')
                alpha = Image.fromarray(alpha_mask, mode='L')
                image = Image.merge('RGBA', (*img_rgb.split(), alpha))
            else:
                # Single band
                alpha_mask = valid_mask[0].astype(np.uint8) * 255
                
                img_gray = Image.fromarray(preview_data[0], mode='L')
                alpha = Image.fromarray(alpha_mask, mode='L')
                # Convert grayscale to RGBA
                image = Image.merge('RGBA', (img_gray, img_gray, img_gray, alpha))
                logger.info("Converted single-band image to RGBA with transparency")
            
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
