from services.utils.googleMaps import travel_time_between_points


# =========================
# חישוב מעבר לקבוצה
# =========================
def calculate_transition(current_location, group, google_maps_service):
    center = group  # כאן נניח שהקבוצה היא נקודת מרכז זמנית

    travel_result = google_maps_service(
        current_location["lat"],
        current_location["lng"],
        center.center_lat,
        center.center_lng
    )

    if "error" in travel_result:
        return None

    return {
        "travel_time": travel_result["duration_min"],
        "distance": travel_result["distance_km"],
        "service_time": getattr(group, "service_time", 10),
        "meals": group.amount_of_meals,
        "group_id": group.id,
        "center_id": group.DistributionCenterID
    }


# =========================
# בדיקת חוקיות מעבר
# =========================
def is_valid_transition(state, transition):
    if transition is None:
        return False

    if state["current_time"] + transition["travel_time"] + transition["service_time"] > state["max_time"]:
        return False

    if state["current_meals"] + transition["meals"] > state["max_meals"]:
        return False

    return True


# =========================
# יצירת מצב חדש
# =========================
def create_new_state(state, group, transition):

    new_state = {
        "current_location": {
            "lat": group.center_lat,
            "lng": group.center_lng
        },

        "current_time": state["current_time"]
        + transition["travel_time"]
        + transition["service_time"],

        "current_meals": state["current_meals"] + transition["meals"],

        "max_time": state["max_time"],
        "max_meals": state["max_meals"],

        "route": state["route"] + [group.id],

        "visited": state["visited"].copy()
    }

    new_state["visited"].add(group.id)

    return new_state


# =========================
# הרחבת מצבים
# =========================
def expand_state(state, groups, google_maps_service):
    new_states = []

    for group in groups:

        if group.id in state["visited"]:
            continue

        transition = calculate_transition(
            state["current_location"],
            group,
            google_maps_service
        )

        if not is_valid_transition(state, transition):
            continue

        new_states.append(
            create_new_state(state, group, transition)
        )

    return new_states