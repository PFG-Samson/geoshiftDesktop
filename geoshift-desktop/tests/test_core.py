import pytest
import numpy as np
import os
from core.analysis_water import compute_ndwi, threshold_water
from core.mask_tools import calculate_area
from core.reader import load_raster
from rasterio.transform import from_origin

def test_compute_ndwi():
    green = np.array([[100, 200], [50, 10]])
    nir = np.array([[50, 10], [100, 200]])
    
    ndwi = compute_ndwi(green, nir)
    
    # (100-50)/(100+50) = 50/150 = 0.33
    assert np.isclose(ndwi[0, 0], 0.333333)
    # (200-10)/(200+10) = 190/210 = 0.90
    assert np.isclose(ndwi[0, 1], 0.904761)
    # (50-100)/(50+100) = -50/150 = -0.33
    assert np.isclose(ndwi[1, 0], -0.333333)

def test_threshold_water():
    ndwi = np.array([[0.1, 0.3], [-0.5, 0.8]])
    mask = threshold_water(ndwi, threshold=0.2)
    
    expected = np.array([[0, 1], [0, 1]])
    np.testing.assert_array_equal(mask, expected)

def test_calculate_area():
    mask = np.array([[1, 1], [0, 1]])
    # Transform: 10m pixel size
    transform = from_origin(0, 0, 10, 10) 
    
    results = calculate_area(mask, transform)
    
    # Pixel area = 10 * 10 = 100 m2
    # True pixels = 3
    # Total area = 300 m2
    assert results['area_m2'] == 300
    # Hectares = 300 / 10000 = 0.03
    assert results['area_ha'] == 0.03
    # Coverage = 3 / 4 = 75%
    assert results['percent_coverage'] == 75.0

# Mock raster loading test would require a sample file or mocking rasterio.open
# Skipping integration test for now in unit tests.
