import time

import httpx

from app.utils.logger import logger

# openstreetmap's nominatim service - genuinely free, no api key, no
# billing account needed at all. the one real requirement is respecting
# their rate limit (max 1 request/second) and identifying our app with
# a real user-agent, not the default one requests libraries send
NOMINATIM_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "FoodDeliveryPlatform/1.0 (student project)"

_last_request_time = 0.0


def _respect_rate_limit() -> None:

    global _last_request_time

    elapsed = time.time() - _last_request_time

    if elapsed < 1.0:

        time.sleep(1.0 - elapsed)

    _last_request_time = time.time()


# converts a real address string into real latitude/longitude, using
# openstreetmap's free nominatim service - no api key required. if the
# request fails for any reason, returns (None, None) rather than
# raising - address creation should never hard-fail just because
# geocoding didn't work
def geocode_address(address_line: str, city: str, pincode: str) -> tuple[float | None, float | None]:

    full_address = f"{address_line}, {city}, {pincode}"

    try:

        _respect_rate_limit()

        response = httpx.get(
            NOMINATIM_GEOCODE_URL,
            params={"q": full_address, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=5.0
        )

        response.raise_for_status()

        results = response.json()

        if not results:

            logger.warning(f"Geocoding returned no results for : {full_address}")

            return None, None

        return float(results[0]["lat"]), float(results[0]["lon"])

    except Exception as error:

        logger.error(f"Geocoding request failed for '{full_address}' : {str(error)}")

        return None, None


# straight-line distance between 2 points, calculated locally using the
# haversine formula - no external api call needed at all for this,
# genuinely free with zero rate limits. this is real distance "as the
# crow flies," not real driving distance/route, which is the one honest
# trade-off versus google's distance matrix api
def calculate_distance_km(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> float:

    from math import radians, sin, cos, sqrt, atan2

    EARTH_RADIUS_KM = 6371.0

    lat1, lon1, lat2, lon2 = map(radians, [origin_lat, origin_lng, dest_lat, dest_lng])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(EARTH_RADIUS_KM * c, 2)