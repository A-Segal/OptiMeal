"""
VRP Solver — Grouped Delivery with Cumulative Meal Capacity

אלגוריתם State Space Search:
חיפוש מלא על כל סדרי הקבוצות האפשריים.
Pruning: דילוג על מצבים שכבר ראינו בזמן טוב יותר.
מטרה: מקסום מספר מנות, בתיקו — מינימום זמן.

הקיבולת היא מצטברת: הרכב יכול לשאת עד max_capacity מנות בסה"כ לאורך כל המסלול.
"""
from copy import deepcopy
from services.vrp.vrp_state import (
    create_initial_state,
    is_feasible,
    get_group_meals,
    apply_move,
    state_key,
)


def solve(
    groups: list,
    start_location: dict,
    max_capacity: int,
    available_time: float,
    google_maps_service,
) -> dict:
    """
    State Space Search — מוצא את המסלול האופטימלי למתנדב.

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

    # ── אתחול ──
    initial_state = create_initial_state(start_location, groups, max_capacity, available_time)

    best_state = deepcopy(initial_state)
    frontier = [initial_state]
    best_seen = {}  # state_key → best_time_seen

    # ── State Space Search ──
    while frontier:
        new_frontier = []

        for s in frontier:
            for group in s["remaining_groups"]:
                # חישוב זמן נסיעה (Google Maps או fallback)
                try:
                    travel_time = google_maps_service(
                        s["current_location"]["lat"],
                        s["current_location"]["lng"],
                        group["center_lat"],
                        group["center_lng"],
                    )
                except Exception:
                    travel_time = 999  # בלתי אפשרי

                # בדיקת feasibility
                if not is_feasible(s, group, travel_time):
                    continue

                # יצירת מצב חדש
                ns = apply_move(s, group, travel_time)

                # Pruning: דילוג על מצב שכבר ראינו בזמן טוב יותר
                key = state_key(ns)
                if key in best_seen and best_seen[key] <= ns["current_time"]:
                    continue
                best_seen[key] = ns["current_time"]

                new_frontier.append(ns)

                # בדיקה — זה המצב הכי טוב?
                if ns["total_meals"] > best_state["total_meals"] or (
                    ns["total_meals"] == best_state["total_meals"]
                    and ns["current_time"] < best_state["current_time"]
                ):
                    best_state = deepcopy(ns)

        frontier = new_frontier

    return {
        "route": best_state["route"],
        "total_meals": best_state["total_meals"],
        "final_time": best_state["current_time"],
        "remaining_capacity": max_capacity - best_state["total_meals"],
    }
