from app.utils.google_maps import calculate_distance_km

def test_distance_between_identical_points_is_zero():
    assert calculate_distance_km(12.9716, 77.5946, 12.9716, 77.5946) == 0.0

def test_distance_calculation_is_reasonable():
    # bengaluru to chennai is roughly 290km in a straight line
    distance = calculate_distance_km(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280 < distance < 300