# geolocation_utils.py
import os
import requests
from math import radians, cos, sin, sqrt, atan2
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY")


# =========================
# פונקציה 1: כתובת -> lat,lng
# =========================
def geocode_address(address: str):
    """
    מקבלת כתובת בעברית או באנגלית
    מחזירה מילון עם latitude ו-longitude
    """
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}&language=iw"
    try:
        response = requests.get(url, verify=False)
    except requests.exceptions.SSLError:
        response = requests.get(url, verify=False)
    data = response.json()

    if data.get("status") != "OK" or not data['results']:
        return {"error": f"כתובת לא נמצאה: {address}"}

    location = data['results'][0]['geometry']['location']
    return {"lat": location['lat'], "lng": location['lng']}


# =========================
# פונקציה 2: מרחק בין שתי נקודות (Haversine)
# =========================
def distance_between_points(lat1, lng1, lat2, lng2):
    """
    מחשב מרחק בקילומטרים בין שתי נקודות
    """
    R = 6371  # רדיוס כדור הארץ בק"מ
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


# =========================
# פונקציה 3: זמן נסיעה בין שתי נקודות (Google Distance Matrix) + CACHE
# =========================
import requests

# מטמון לזמני נסיעה — חוסך קריאות חוזרות ל-Google
_travel_cache: dict[tuple, float] = {}
_session = None

_TRANSIENT_MATRIX_STATUSES = {"OVER_QUERY_LIMIT", "UNKNOWN_ERROR"}


def _should_cache_failure(status: str) -> bool:
    if not status:
        return False
    return status not in _TRANSIENT_MATRIX_STATUSES


def _get_http_session():
    global _session
    if _session is not None:
        return _session
    session = requests.Session()
    retry_kwargs = {
        "total": 2,
        "connect": 2,
        "read": 2,
        "backoff_factor": 0.2,
        "status_forcelist": (429, 500, 502, 503, 504),
    }
    try:
        # urllib3 >= 1.26
        retry = Retry(allowed_methods=frozenset(["GET"]), **retry_kwargs)
    except TypeError:
        # urllib3 < 1.26 compatibility
        retry = Retry(method_whitelist=frozenset(["GET"]), **retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    _session = session
    return _session


def travel_time_between_points(lat1, lng1, lat2, lng2, mode="driving"):
    # מפתח cache מעוגל ל-4 ספרות (דיוק של ~11 מטר)
    key = (round(lat1, 5), round(lng1, 5), round(lat2, 5), round(lng2, 5), mode)

    # בדיקה במטמון — כיוון ישיר
    if key in _travel_cache:
        return _travel_cache[key]

    origins = f"{lat1},{lng1}"
    destinations = f"{lat2},{lng2}"

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origins}&destinations={destinations}"
        f"&mode={mode}&key={API_KEY}"
    )

    session = _get_http_session()
    try:
        response = session.get(url, timeout=15)
    except requests.exceptions.SSLError:
        response = session.get(url, timeout=15, verify=False)
    data = response.json()

    matrix_status = data.get("status")
    if matrix_status != 'OK':
        if _should_cache_failure(matrix_status):
            _travel_cache[key] = 999999
        return 999999

    element = data['rows'][0]['elements'][0]

    element_status = element.get("status")
    if element_status != 'OK':
        if _should_cache_failure(element_status):
            _travel_cache[key] = 999999
        return 999999

    result = element['duration']['value'] / 60
    _travel_cache[key] = result
    return result

# =========================
# פונקציה 4: קבלת אזור/יישוב/מחוז
# =========================
def get_region_from_address(address: str):
    """
    מחזיר את העיר/יישוב/מחוז של כתובת
    """
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}&language=iw"
    response = requests.get(url)
    data = response.json()

    if data['status'] != 'OK' or not data['results']:
        return {"error": "כתובת לא נמצאה"}

    components = data['results'][0]['address_components']
    region = {"city": None, "administrative_area": None, "country": None}

    for comp in components:
        if "locality" in comp['types']:
            region['city'] = comp['long_name']
        elif "administrative_area_level_1" in comp['types']:
            region['administrative_area'] = comp['long_name']
        elif "country" in comp['types']:
            region['country'] = comp['long_name']

    return region

# =========================
# פונקציה 5: Reverse Geocode — lat,lng → city
# =========================
def reverse_geocode_region(lat: float, lng: float):
    """
    מחזיר את העיר/יישוב/מחוז של קואורדינטות (reverse geocode).
    """
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lng}&key={API_KEY}&language=iw"
    )
    try:
        response = requests.get(url, verify=False)
    except requests.exceptions.SSLError:
        response = requests.get(url, verify=False)
    data = response.json()

    if data.get("status") != "OK" or not data.get("results"):
        return {"city": None, "administrative_area": None, "country": None}

    components = data["results"][0].get("address_components", [])
    region = {"city": None, "administrative_area": None, "country": None}

    for comp in components:
        types = comp.get("types", [])
        if "locality" in types:
            region["city"] = comp["long_name"]
        elif "administrative_area_level_1" in types:
            region["administrative_area"] = comp["long_name"]
        elif "country" in types:
            region["country"] = comp["long_name"]

    return region


def reverse_geocode_address(lat: float, lng: float):
    """
    מחזיר כתובת מלאה של קואורדינטות (reverse geocode).
    במקרה של כשלון מחזיר None.
    """
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lng}&key={API_KEY}&language=iw"
    )

    try:
        response = requests.get(url, verify=False)
    except requests.exceptions.SSLError:
        response = requests.get(url, verify=False)
    except Exception:
        return None

    data = response.json()
    if data.get("status") != "OK" or not data.get("results"):
        return None

    top = data["results"][0]
    return top.get("formatted_address")


def safe_travel_time(lat1, lng1, lat2, lng2, google_maps_service):
    try:
        result = google_maps_service(lat1, lng1, lat2, lng2)

        if isinstance(result, dict):
            return result.get("duration_min", 999)

        if isinstance(result, (int, float)):
            return float(result)

        return 999

    except:
        return 999