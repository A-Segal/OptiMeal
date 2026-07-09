# geolocation_utils.py
import os
import requests
from math import radians, cos, sin, sqrt, atan2

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
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "OK" or not data['results']:
        return {"error": "כתובת לא נמצאה"}

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


def travel_time_between_points(lat1, lng1, lat2, lng2, mode="driving"):
    import requests

    # מפתח cache מעוגל ל-4 ספרות (דיוק של ~11 מטר)
    key = (round(lat1, 4), round(lng1, 4), round(lat2, 4), round(lng2, 4))

    # בדיקה במטמון — כיוון ישיר
    if key in _travel_cache:
        return _travel_cache[key]

    # בדיקה במטמון — כיוון הפוך (זמן נסיעה דומה)
    rev_key = (key[2], key[3], key[0], key[1])
    if rev_key in _travel_cache:
        return _travel_cache[rev_key]

    print("CALLING GOOGLE MAPS:", key)

    origins = f"{lat1},{lng1}"
    destinations = f"{lat2},{lng2}"

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origins}&destinations={destinations}"
        f"&mode={mode}&key={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    if data.get('status') != 'OK':
        _travel_cache[key] = 999999
        return 999999

    element = data['rows'][0]['elements'][0]

    if element.get('status') != 'OK':
        _travel_cache[key] = 999999
        return 999999

    result = element['duration']['value'] / 60
    _travel_cache[key] = result
    return result

# =========================
# פונקציה 4: lat,lng → כתובת (Reverse Geocoding)
# =========================
_reverse_cache: dict[tuple, str] = {}

def reverse_geocode(lat, lng):
    """מקבלת lat,lng — מחזירה מחרוזת כתובת בעברית (עם cache)."""
    key = (round(float(lat), 5), round(float(lng), 5))
    if key in _reverse_cache:
        return _reverse_cache[key]
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={API_KEY}&language=iw"
    try:
        data = requests.get(url, timeout=5).json()
        if data.get("status") == "OK" and data.get("results"):
            addr = data["results"][0].get("formatted_address", "")
            _reverse_cache[key] = addr
            return addr
    except:
        pass
    _reverse_cache[key] = ""
    return ""


# =========================
# פונקציה 5: קבלת אזור/יישוב/מחוז
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