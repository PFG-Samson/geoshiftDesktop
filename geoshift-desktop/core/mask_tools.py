import numpy as np

def calculate_area(mask, transform):
    """
    Calculates the area of the mask (value 1) in square meters and hectares.
    Assumes transform is an Affine object from rasterio.
    """
    # Pixel size
    # transform.a is pixel width (x), transform.e is pixel height (y, usually negative)
    pixel_area_m2 = abs(transform.a * transform.e)
    
    # Count pixels
    true_pixels = np.sum(mask == 1)
    
    water_area_m2 = pixel_area_m2 * true_pixels
    water_area_ha = water_area_m2 / 10000.0
    
    total_pixels = mask.size
    percent_coverage = (true_pixels / total_pixels) * 100
    
    return {
        "area_m2": water_area_m2,
        "area_ha": water_area_ha,
        "percent_coverage": percent_coverage
    }
