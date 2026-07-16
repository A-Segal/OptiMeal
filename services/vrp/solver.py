"""
VRP Solver — Grouped Delivery with Cumulative Meal Capacity

Algorithm: Branch & Bound + Greedy Nearest Neighbor initial solution.
Finds the globally optimal route: maximize meals, then same-city groups, then minimize time.

- Greedy NN: fast first solution → excellent initial upper bound
- Branch & Bound: recursive DFS with optimistic pruning → guarantees optimality
- Pruning criterion: current_meals + optimistic_remaining_meals <= best_meals → skip branch

הקיבולת היא מצטברת: הרכב יכול לשאת עד max_capacity מנות בסה"כ לאורך כל המסלול.
"""
from copy import deepcopy
from services.vrp.vrp_state import (
    create_initial_state,
    is_feasible,
    get_group_meals,
    get_group_families,
    get_group_service_time,
    get_ordered_group_recipients,
    apply_move,
    state_key,
    estimate_remaining_meals_tight,
)


def solve(
    groups: list,
    start_location: dict,
    max_capacity: int,
    available_time: float,
    google_maps_service,
    preferred_city: str = None,
    group_cities: dict = None,
    same_city_bonus_minutes: float = 15.0,
) -> dict:
    """
    Branch & Bound — מוצא את המסלול האופטימלי למתנדב.

    Parameters
    ----------
    groups : list[dict]
        רשימת קבוצות (מבנה מ-build_groups).
    start_location : dict
        מיקום התחלתי {"lat": ..., "lng": ...}.
    max_capacity : int
        קיבולת הרכב במנות (מקסימום מנות מצטברות למסלול).
    available_time : float
        זמן פנוי של המתנדב (בדקות).
    google_maps_service : callable
        פונקציית Google Distance Matrix (מקבלת lat1,lng1,lat2,lng2, מחזירה דקות).
    preferred_city : str | None
        העיר של המתנדב. כאשר מועבר, המסלול יעדיף קבוצות באותה עיר.
    group_cities : dict | None
        מיפוי center_id → city. נדרש כש-preferred_city מועבר.
    same_city_bonus_minutes : float
        בכמה "דקות וירטואליות" להעדיף קבוצה מאותה עיר (default: 15).

    Returns
    -------
    dict : {
        "route": list[center_id],
        "total_meals": int,
        "final_time": float,
        "remaining_capacity": int
    }
    """
    if not groups:
        return {
            "route": [],
            "total_meals": 0,
            "final_time": 0.0,
            "remaining_capacity": max_capacity,
        }

    # Per-solve cache to avoid repeated travel-time calls during search.
    travel_time_cache = {}
    diagnostics = {
        "infeasible_google": 0,
        "infeasible_time": 0,
        "infeasible_capacity": 0,
        "infeasible_visited": 0,
        "infeasible_empty_group": 0,
        "feasible_checks": 0,
    }

    def infeasibility_reason(state, group, travel_time):
        if travel_time >= 999:
            return "google"
        service_time = get_group_service_time(group)
        group_meals = get_group_meals(group)
        group_families = get_group_families(group)
        if state["current_time"] + travel_time + service_time > state["available_time"]:
            return "time"
        if state["total_meals"] + group_meals > state["max_capacity"]:
            return "capacity"
        if group["center_id"] in state["visited_groups"]:
            return "visited"
        if group_families == 0:
            return "empty_group"
        return None

    def record_reason(reason):
        if reason == "google":
            diagnostics["infeasible_google"] += 1
        elif reason == "time":
            diagnostics["infeasible_time"] += 1
        elif reason == "capacity":
            diagnostics["infeasible_capacity"] += 1
        elif reason == "visited":
            diagnostics["infeasible_visited"] += 1
        elif reason == "empty_group":
            diagnostics["infeasible_empty_group"] += 1

    def cached_travel_time(lat1, lng1, lat2, lng2):
        key = (
            round(float(lat1), 6),
            round(float(lng1), 6),
            round(float(lat2), 6),
            round(float(lng2), 6),
        )
        if key in travel_time_cache:
            return travel_time_cache[key]
        try:
            value = google_maps_service(lat1, lng1, lat2, lng2)
        except Exception:
            value = 999
        if not isinstance(value, (int, float)):
            value = 999
        value = float(value)
        travel_time_cache[key] = value
        return value

    def group_transition_time(current_location, group):
        total_travel = cached_travel_time(
            current_location["lat"],
            current_location["lng"],
            group["center_lat"],
            group["center_lng"],
        )

        previous_location = {
            "lat": group["center_lat"],
            "lng": group["center_lng"],
        }
        for _, recipient_location in get_ordered_group_recipients(group, current_location):
            total_travel += cached_travel_time(
                previous_location["lat"],
                previous_location["lng"],
                recipient_location["lat"],
                recipient_location["lng"],
            )
            previous_location = recipient_location

        return total_travel

    # ── City preference map ──
    same_city_map = {}
    if preferred_city and group_cities:
        same_city_map = {
            g["center_id"]: (group_cities.get(g["center_id"], "") == preferred_city)
            for g in groups
        }

    def count_same_city_centers(route):
        if not same_city_map:
            return 0
        return sum(1 for cid in route if same_city_map.get(cid, False))

    def is_better(ns, best):
        """True if ns is better than best: more meals > more same-city > less time."""
        if ns["total_meals"] > best["total_meals"]:
            return True
        if ns["total_meals"] < best["total_meals"]:
            return False
        ns_city = count_same_city_centers(ns["route"])
        best_city = count_same_city_centers(best["route"])
        if ns_city > best_city:
            return True
        if ns_city < best_city:
            return False
        return ns["current_time"] < best["current_time"]

    # ── Greedy NN: fast initial solution ──
    def _greedy_nn_run(start_groups, initial_state):
        """Run greedy NN from a specific starting group order."""
        s = deepcopy(initial_state)
        remaining = list(start_groups) if start_groups else list(s["remaining_groups"])
        while remaining:
            best_group = None
            best_travel = float("inf")
            # Try each remaining group, pick the one with best travel time
            for g in remaining:
                tt = group_transition_time(s["current_location"], g)
                diagnostics["feasible_checks"] += 1
                if not is_feasible(s, g, tt):
                    record_reason(infeasibility_reason(s, g, tt))
                    continue
                # Prefer groups with more meals for same travel, and same-city groups
                score = tt
                if same_city_map and same_city_map.get(g["center_id"]):
                    score -= same_city_bonus_minutes  # virtual discount for same city
                if score < best_travel:
                    best_travel = score
                    best_group = g
            if best_group is None:
                break
            s = apply_move(s, best_group, best_travel)
            remaining = [g for g in remaining if g["center_id"] != best_group["center_id"]]
        return s

    # Try several greedy starting orders to get a good initial solution
    initial = create_initial_state(start_location, groups, max_capacity, available_time)
    best_state = deepcopy(initial)

    # Run greedy NN (natural order) as baseline
    greedy_result = _greedy_nn_run([], initial)
    if is_better(greedy_result, best_state):
        best_state = deepcopy(greedy_result)

    # Also try greedy starting from each group as first (better coverage)
    for i, first_group in enumerate(groups):
        reordered = [first_group] + [g for j, g in enumerate(groups) if j != i]
        greedy_result = _greedy_nn_run(reordered, initial)
        if is_better(greedy_result, best_state):
            best_state = deepcopy(greedy_result)

    best_seen = {}  # state_key → best_time_seen

    # ── Branch & Bound: recursive DFS ──
    def _bb_search(state):
        nonlocal best_state, best_seen

        # Prune: optimistic bound — can we even beat or tie best_meals?
        optimistic_meals = state["total_meals"] + estimate_remaining_meals_tight(state)
        # Use <= because even if we tie on meals, we'd need same-city or time advantage
        # which is unlikely if the bound is far. Use a small epsilon for float safety.
        if optimistic_meals < best_state["total_meals"] - 0.01:
            return

        # If current_meals already below best and can only tie — prune unless
        # same-city could save us. (Minor: we still explore — tight bound handles most.)

        # Score each remaining group for ordering: meals per minute + same-city bonus
        scored = []
        for g in state["remaining_groups"]:
            tt = group_transition_time(state["current_location"], g)

            diagnostics["feasible_checks"] += 1
            if not is_feasible(state, g, tt):
                record_reason(infeasibility_reason(state, g, tt))
                continue

            # Heuristic: higher meals + same-city = explore first (better pruning)
            meals = get_group_meals(g)
            city_bonus = same_city_bonus_minutes if same_city_map.get(g["center_id"]) else 0
            # Score = meals per effective minute (with city bonus reducing effective time)
            eff_time = max(tt - city_bonus, 1.0)
            priority = meals / eff_time
            scored.append((priority, g, tt))

        # Sort descending by priority — best prospects first
        scored.sort(key=lambda x: x[0], reverse=True)

        for _, group, travel_time in scored:
            ns = apply_move(state, group, travel_time)

            # Prune: state dominance
            key = state_key(ns)
            if key in best_seen and best_seen[key] <= ns["current_time"]:
                continue
            best_seen[key] = ns["current_time"]

            # Update best
            if is_better(ns, best_state):
                best_state = deepcopy(ns)

            # Recurse deeper
            _bb_search(ns)

    # Run B&B from initial state
    _bb_search(initial)

    return {
        "route": best_state["route"],
        "total_meals": best_state["total_meals"],
        "final_time": best_state["current_time"],
        "remaining_capacity": max_capacity - best_state["total_meals"],
        "diagnostics": diagnostics,
    }
