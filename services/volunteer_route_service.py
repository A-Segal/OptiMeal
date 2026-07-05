from services.vrp.solver import solve
from services.vrp.vrp_state import get_group_families, VEHICLE_CAPACITY, get_ordered_group_recipients
from services.utils.googleMaps import (
    geocode_address,
    travel_time_between_points
)


def get_capacity(vehicle_type):
    return VEHICLE_CAPACITY.get(vehicle_type, 3)


# =========================
# FLATTEN ROUTE FOR REACT
# =========================
def build_detailed_route(route, groups, start_location):
    group_map = {g["center_id"]: g for g in groups}

    full_route = []
    current_location = start_location

    # START POINT
    full_route.append({
        "step": 0,
        "type": "start",
        "center_id": None,
        "assignment_id": None,
        "lat": start_location["lat"],
        "lng": start_location["lng"]
    })

    step = 1

    for center_id in route:
        group = group_map.get(center_id)
        if not group:
            continue

        # CENTER
        full_route.append({
            "step": step,
            "type": "center",
            "center_id": center_id,
            "assignment_id": None,
            "lat": group["center_lat"],
            "lng": group["center_lng"]
        })
        step += 1

        # RECIPIENTS (ordered inside group by proximity)
        ordered_recipients = get_ordered_group_recipients(group, current_location)
        for aid, loc in ordered_recipients:
            full_route.append({
                "step": step,
                "type": "recipient",
                "center_id": center_id,
                "assignment_id": aid,
                "lat": loc["lat"],
                "lng": loc["lng"]
            })
            step += 1
            current_location = loc

    return full_route


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
        return {
            "volunteer_id": volunteer.id,
            "start_location": start_location,
            "route": [],
            "detailed_route": [],
            "message": "no groups available"
        }

    # 4. VEHICLE CAPACITY
    vehicle = getattr(volunteer, "vehicle", None)
    # vehicle.capacity = סוג הרכב (1-5)
    vehicle_type = getattr(vehicle, "capacity", 3) if vehicle else 3
    vehicle_capacity = get_capacity(vehicle_type)

    # 5. AVAILABLE TIME — המרה משעות לדקות
    if available_time is not None:
        available_time_minutes = available_time * 60  # שעות → דקות
    else:
        available_time_minutes = 999999  # אין הגבלה

    print(f"Available time: {available_time_minutes} min (from {available_time} hours)")

    # 6. SOLVER
    result = solve(
        groups=groups,
        start_location=start_location,
        max_capacity=vehicle_capacity,
        available_time=available_time_minutes,
        google_maps_service=travel_time_between_points
    )

    if not result:
        return {"error": "solver failed"}

    route = result.get("route", [])

    if not route:
        return {
            "volunteer_id": volunteer.id,
            "start_location": start_location,
            "route": [],
            "detailed_route": [],
            "message": "no feasible route found"
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
        "vehicle_capacity": vehicle_capacity,
        "total_deliveries": result.get("total_deliveries", 0),
        "final_time_minutes": result.get("final_time", 0),
        "visited_count": len(route)
    }
