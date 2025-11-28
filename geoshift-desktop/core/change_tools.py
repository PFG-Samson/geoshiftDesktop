import numpy as np
from typing import Dict

def calculate_change_area(mask_before: np.ndarray, mask_after: np.ndarray, transform) -> Dict:
    """
    Calculate the area of change between two masks.
    """
    # Pixel size
    pixel_area_m2 = abs(transform.a * transform.e)
    
    # Count changes
    before_pixels = np.sum(mask_before > 0)
    after_pixels = np.sum(mask_after > 0)
    
    # Calculate areas
    before_area_m2 = pixel_area_m2 * before_pixels
    after_area_m2 = pixel_area_m2 * after_pixels
    change_area_m2 = abs(after_area_m2 - before_area_m2)
    
    # Convert to hectares
    before_area_ha = before_area_m2 / 10000.0
    after_area_ha = after_area_m2 / 10000.0
    change_area_ha = change_area_m2 / 10000.0
    
    total_pixels = mask_before.size
    change_percentage = (change_area_m2 / (pixel_area_m2 * total_pixels)) * 100
    
    return {
        "before_area_m2": before_area_m2,
        "before_area_ha": before_area_ha,
        "after_area_m2": after_area_m2,
        "after_area_ha": after_area_ha,
        "change_area_m2": change_area_m2,
        "change_area_ha": change_area_ha,
        "change_percentage": change_percentage,
        "change_type": "gain" if after_pixels > before_pixels else "loss" if after_pixels < before_pixels else "no-change"
    }

def generate_change_map(mask_a: np.ndarray, mask_b: np.ndarray) -> np.ndarray:
    """
    Generate a color-coded change map.
    Red = loss, Green = gain, Yellow = modified, Gray = no change
    """
    # Create RGB change map
    h, w = mask_a.shape[:2]
    change_map = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Normalize masks to binary
    mask_a_bin = (mask_a > 0).astype(np.uint8)
    mask_b_bin = (mask_b > 0).astype(np.uint8)
    
    # Loss: in A but not in B (Red)
    loss = (mask_a_bin == 1) & (mask_b_bin == 0)
    change_map[loss] = [255, 0, 0]
    
    # Gain: in B but not in A (Green)
    gain = (mask_a_bin == 0) & (mask_b_bin == 1)
    change_map[gain] = [0, 255, 0]
    
    # Modified: in both (Yellow)
    modified = (mask_a_bin == 1) & (mask_b_bin == 1)
    change_map[modified] = [255, 255, 0]
    
    return change_map

def classify_change_type(diff_mask: np.ndarray) -> str:
    """
    Classify the type of change based on the difference mask.
    """
    change_pixels = np.sum(diff_mask > 0)
    total_pixels = diff_mask.size
    change_ratio = change_pixels / total_pixels
    
    if change_ratio < 0.01:
        return "minimal"
    elif change_ratio < 0.1:
        return "moderate"
    else:
        return "significant"
