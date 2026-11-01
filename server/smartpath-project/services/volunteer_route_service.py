from services.vrp.solver import solve
from services.vrp.vrp_state import get_group_families, get_group_meals, get_group_service_time, VEHICLE_CAPACITY, get_ordered_group_recipients
from repository.VehicleRepository import VehicleRepository
from services.utils.googleMaps import (
    geocode_address,
    travel_time_between_points,
    safe_travel_time,
    distance_between_points,
    reverse_geocode_region,
    reverse_geocode_address,
)


def get_capacity(vehicle_type):
    """מחזיר קיבולת רכב במנות לפי סוג הרכב (1-5)."""
    return VEHICLE_CAPACITY.get(vehicle_type, 120)  # default = פרטי


def _fallback_travel_time_minutes(lat1, lng1, lat2, lng2):
    """
    Fallback לזמן נסיעה בדקות במקרה ש-Google לא מחזיר תשובה תקינה.
    משתמש בקירוב של 35 קמ"ש בתוך עיר + 3 דק' מרווח תפעולי.
    """
    km = distance_between_points(lat1, lng1, lat2, lng2)
    return (km / 35.0) * 60.0 + 3.0


STRICT_GOOGLE_TRAVEL_TIMES = True


# =========================
# FLATTEN ROUTE FOR REACT
# =========================
def build_detailed_route(route, groups, start_location):
    """
    בונה מסלול מפורט עם כל המידע שהמתנדב צריך:
    - שמות נזקקים, כמויות מנות
    - שמות מרכזי חלוקה
    - action: pickup / deliver
    """
    group_map = {g["center_id"]: g for g in groups}

    # Cache reverse-geocoded addresses per rounded coordinate to reduce API calls.
    address_cache = {}

    def _step_address(lat, lng):
        key = (round(float(lat), 5), round(float(lng), 5))
        if key in address_cache:
            return address_cache[key]
        addr = reverse_geocode_address(lat, lng)
        address_cache[key] = addr
        return addr

    full_route = []
    current_location = start_location

    # ── START ──
    full_route.append({
        "step": 0,
        "type": "start",
        "action": "start",
        "center_id": None,
        "assignment_id": None,
        "lat": start_location["lat"],
        "lng": start_location["lng"],
        "label": "נקודת התחלה",
        "detail": "",
        "address": _step_address(start_location["lat"], start_location["lng"]),
        "meals": 0,
    })

    step = 1

    for center_id in route:
        group = group_map.get(center_id)
        if not group:
            continue

        center_name = group.get("center_name", f"מרכז חלוקה #{center_id}")
        center_total_meals = group.get("total_meals", 0)

        # ── CENTER (איסוף) ──
        full_route.append({
            "step": step,
            "type": "center",
            "action": "pickup",
            "center_id": center_id,
            "assignment_id": None,
            "lat": group["center_lat"],
            "lng": group["center_lng"],
            "label": center_name,
            "detail": f"איסוף — {center_total_meals} מנות",
            "address": _step_address(group["center_lat"], group["center_lng"]),
            "meals": center_total_meals,
        })
        step += 1

        # ── RECIPIENTS (חלוקה) ──
        ordered_recipients = get_ordered_group_recipients(group, current_location)
        recipient_names = group.get("recipient_names", [])
        recipient_meals = group.get("recipient_meals", [])
        # map: assignment_id → index
        assignment_ids = group.get("assignment_ids", [])

        for aid, loc in ordered_recipients:
            # find index for this assignment_id
            idx = assignment_ids.index(aid) if aid in assignment_ids else -1
            recip_name = recipient_names[idx] if 0 <= idx < len(recipient_names) else f"משפחה #{aid}"
            recip_meals = recipient_meals[idx] if 0 <= idx < len(recipient_meals) else 0

            full_route.append({
                "step": step,
                "type": "recipient",
                "action": "deliver",
                "center_id": center_id,
                "assignment_id": aid,
                "lat": loc["lat"],
                "lng": loc["lng"],
                "label": recip_name,
                "detail": f"חלוקה — {recip_meals} מנות",
                "address": _step_address(loc["lat"], loc["lng"]),
                "meals": recip_meals,
            })
            step += 1
            current_location = loc

    return full_route


def calculate_actual_route_minutes(route, groups, start_location, travel_time_service):
    group_map = {g["center_id"]: g for g in groups}
    current_location = start_location
    total_minutes = 0.0

    for center_id in route:
        group = group_map.get(center_id)
        if not group:
            continue

        total_minutes += travel_time_service(
            current_location["lat"],
            current_location["lng"],
            group["center_lat"],
            group["center_lng"],
        )

        previous_location = {
            "lat": group["center_lat"],
            "lng": group["center_lng"],
        }
        ordered_recipients = get_ordered_group_recipients(group, current_location)
        for _, recipient_location in ordered_recipients:
            total_minutes += travel_time_service(
                previous_location["lat"],
                previous_location["lng"],
                recipient_location["lat"],
                recipient_location["lng"],
            )
            previous_location = recipient_location

        total_minutes += get_group_service_time(group)
        current_location = previous_location

    return total_minutes


# =========================
# MAIN SERVICE
# =========================
def run_volunteer_route(
    volunteer_id,
    volunteer_repo,
    assignment_repo,
    google_maps_service=None,
    start_address=None,
    start_location_param=None,
    available_time=None,
):
    """
    מריץ את אלגוריתם ה-VRP עבור מתנדב.

    Parameters
    ----------
    start_address : str | None
        כתובת טקסטואלית. עובר geocoding.
    start_location_param : dict | None
        מיקום מוכן {"lat": ..., "lng": ...}. עוקף את ה-geocoding.
    available_time : float | None
        זמן פנוי בשעות. אם None — משתמש ב-default גבוה (אין הגבלת זמן).
    """
    print("=== START ROUTE DEBUG ===")

    # 1. VOLUNTEER
    volunteer = volunteer_repo.get_volunteer(volunteer_id)
    if not volunteer:
        return {"error": "volunteer not found"}

    # 2. START LOCATION
    if start_address:
        geo = geocode_address(start_address)
        if not geo or "error" in geo:
            return {"error": "geocode failed", "details": geo}

        start_location = {"lat": geo["lat"], "lng": geo["lng"]}
    elif start_location_param is not None:
        start_location = start_location_param
    else:
        return {"error": "no start location — provide address or location"}

    # 3. GROUPS
    groups = assignment_repo.build_groups()

    groups = [
        g for g in groups
        if isinstance(g, dict)
        and g.get("center_id")
        and g.get("center_lat")
        and g.get("center_lng")
    ]

    if not groups:
        no_unassigned_left = False
        try:
            no_unassigned_left = not assignment_repo.has_unassigned_assignments()
        except Exception:
            no_unassigned_left = False

        message = (
            "תודה! כל הארוחות כבר שובצו למתנדבים"
            if no_unassigned_left
            else "אין כרגע קבוצות זמינות לשיבוץ"
        )
        return {
            "volunteer_id": volunteer.id,
            "start_location": start_location,
            "route": [],
            "detailed_route": [],
            "message": message
        }

    # 4. VEHICLE CAPACITY — במנות
    vehicle = VehicleRepository(volunteer_repo.db).get_by_volunteer_id(volunteer.id)
    # vehicle.capacity = סוג הרכב (1-5)
    vehicle_type = int(getattr(vehicle, "capacity", 3)) if vehicle else 3
    vehicle_capacity = get_capacity(vehicle_type)  # קיבולת במנות

    # 5. AVAILABLE TIME — המרה משעות לדקות
    try:
        available_time_num = float(available_time) if available_time is not None else None
    except (TypeError, ValueError):
        available_time_num = None

    if available_time_num is not None and available_time_num > 0:
        available_time_minutes = available_time_num * 60  # שעות → דקות
    else:
        available_time_minutes = 999999  # אין הגבלה

    print(f"Available time: {available_time_minutes} min (from {available_time} hours)")
    print(f"Vehicle capacity: {vehicle_capacity} meals (type {vehicle_type})")

    # 5b. CITY PREFERENCE — reverse geocode start location + group centers
    volunteer_city = None
    group_cities = {}
    if groups:
        try:
            geo_start = reverse_geocode_region(start_location["lat"], start_location["lng"])
            volunteer_city = geo_start.get("city") if isinstance(geo_start, dict) else None
            print(f"Volunteer city: {volunteer_city}")
        except Exception:
            pass

        # City of each group center
        for g in groups:
            try:
                geo = reverse_geocode_region(g["center_lat"], g["center_lng"])
                if isinstance(geo, dict):
                    city = geo.get("city")
                    if city:
                        group_cities[g["center_id"]] = city
            except Exception:
                pass

        if volunteer_city:
            same_city_count = sum(1 for c in group_cities.values() if c == volunteer_city)
            print(f"Groups in same city ({volunteer_city}): {same_city_count}/{len(groups)}")

    # 6. SOLVER
    routing_service = google_maps_service or travel_time_between_points

    def robust_travel_time(lat1, lng1, lat2, lng2):
        minutes = safe_travel_time(lat1, lng1, lat2, lng2, routing_service)
        if minutes >= 999:
            if STRICT_GOOGLE_TRAVEL_TIMES:
                return 999
            return _fallback_travel_time_minutes(lat1, lng1, lat2, lng2)
        return minutes

    result = solve(
        groups=groups,
        start_location=start_location,
        max_capacity=vehicle_capacity,
        available_time=available_time_minutes,
        google_maps_service=robust_travel_time,
        preferred_city=volunteer_city,
        group_cities=group_cities,
    )

    if not result:
        return {"error": "solver failed"}

    route = result.get("route", [])

    if not route:
        diagnostics = result.get("diagnostics", {}) if isinstance(result, dict) else {}
        return {
            "volunteer_id": volunteer.id,
            "start_location": start_location,
            "route": [],
            "detailed_route": [],
            "message": "לא נמצא מסלול מתאים לזמן ולקיבולת שהוגדרו",
            "diagnostics": diagnostics,
        }

    actual_route_minutes = calculate_actual_route_minutes(
        route=route,
        groups=groups,
        start_location=start_location,
        travel_time_service=robust_travel_time,
    )

    if actual_route_minutes > available_time_minutes + 0.01:
        return {
            "volunteer_id": volunteer.id,
            "start_location": start_location,
            "route": [],
            "detailed_route": [],
            "message": "לא נמצא מסלול מתאים לזמן ולקיבולת שהוגדרו",
            "diagnostics": {
                **(result.get("diagnostics", {}) if isinstance(result, dict) else {}),
                "available_time_minutes": available_time_minutes,
                "actual_route_minutes": actual_route_minutes,
                "time_validation_failed": True,
            },
        }

    # 7. BUILD UI ROUTE
    detailed_route = build_detailed_route(route, groups, start_location)

    # 8. ASSIGNMENTS
    for g in groups:
        if g["center_id"] in route:
            for assignment_id in g.get("assignment_ids", []):
                assignment = assignment_repo.get_delivery_assignment(assignment_id)
                if assignment and assignment.VolunteerID is None:
                    assignment_repo.assign_volunteer_to_group(
                        assignment_id,
                        volunteer_id
                    )

    # 9. RESPONSE
    return {
        "volunteer_id": volunteer.id,
        "start_location": start_location,
        "route": route,
        "detailed_route": detailed_route,
        "groups_count": len(groups),
        "vehicle_capacity": vehicle_capacity,          # קיבולת במנות
        "total_meals": result.get("total_meals", 0),   # סה"כ מנות במסלול
        "final_time_minutes": actual_route_minutes,
        "visited_count": len(route)
    }
