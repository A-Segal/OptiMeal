def create_initial_state(volunteer, start_location, available_time, max_capacity):
    return {
        "current_location": start_location,
        "current_time": 0,
        "current_meals": 0,

        "max_time": available_time,
        "max_meals": max_capacity,

        "route": [],
        "visited": set()
    }