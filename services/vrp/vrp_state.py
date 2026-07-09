"""
VRP State Module — Grouped Delivery with Cumulative Meal Capacity

מייצג מצב בחיפוש, בדיקות feasibility, וחישובי קבוצות.
כל קבוצה = מרכז חלוקה + הנזקקים המשויכים אליו.

הקיבולת נבדקת באופן מצטבר על כל המסלול:
הרכב יכול לשאת עד max_capacity מנות בסה"כ — לא משנה מאיזה מרכז.
"""
import math
from copy import deepcopy


# ---------------------------------------------------------------------------
# קיבולות רכב — טבלה קבועה לפי סוג הרכב (במנות)
# ---------------------------------------------------------------------------
VEHICLE_CAPACITY = {
    1: 20,    # אופנוע
    2: 60,    # Mini
    3: 120,   # Private
    4: 250,   # Station
    5: 500,   # מסחרי
}

# זמן עיבוד פנימי לקבוצה (דקות) — איסוף מהמרכז + חלוקה לנזקקים
SERVICE_TIME_PER_FAMILY = 5  # דקות למשפחה


def get_vehicle_capacity(vehicle_type: int) -> int:
    """מחזיר קיבולת רכב (מספר מנות מקסימלי) לפי סוג."""
    return VEHICLE_CAPACITY.get(vehicle_type, 120)  # default = פרטי


# ---------------------------------------------------------------------------
# עזר — חישוב משפחות בקבוצה
# ---------------------------------------------------------------------------
def get_group_families(group: dict) -> int:
    """
    מחזיר את מספר המשפחות בקבוצה.
    משתמש ב-group_families אם קיים, אחרת נופל לאורך רשימת הנמענים.
    """
    if "group_families" in group and group["group_families"] is not None:
        return group["group_families"]
    recipients = group.get("recipients_locations", [])
    if recipients:
        return len(recipients)
    return group.get("total_meals", 0)  # fallback


def get_group_meals(group: dict) -> int:
    """מחזיר את סך המנות בקבוצה."""
    return group.get("total_meals", 0)


def get_group_service_time(group: dict) -> float:
    """זמן שירות לקבוצה: 5 דקות למשפחה."""
    return get_group_families(group) * SERVICE_TIME_PER_FAMILY


# ---------------------------------------------------------------------------
# Haversine — מרחק בק"מ
# ---------------------------------------------------------------------------
def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ---------------------------------------------------------------------------
# סידור נמענים בתוך קבוצה לפי קרבה (Nearest Neighbor)
# ---------------------------------------------------------------------------
def get_ordered_group_recipients(group: dict, from_location: dict = None):
    """
    סידור נמענים בתוך קבוצת משלוח לפי קרבה למיקום הנוכחי,
    כך שהמסלול יעבור בכתובות בסדר גיאוגרפי הגיוני.
    """
    assignment_ids = group.get("assignment_ids", [])
    recipients = group.get("recipients_locations", [])

    if not recipients:
        return []

    pairs = list(zip(assignment_ids, recipients))
    if len(pairs) <= 1:
        return pairs

    start_location = from_location or {
        "lat": group.get("center_lat", 0.0),
        "lng": group.get("center_lng", 0.0),
    }

    remaining = list(pairs)
    ordered = []
    current_location = start_location

    while remaining:
        best_index = min(
            range(len(remaining)),
            key=lambda idx: _distance_km(
                current_location["lat"],
                current_location["lng"],
                remaining[idx][1]["lat"],
                remaining[idx][1]["lng"],
            ),
        )
        selected = remaining.pop(best_index)
        ordered.append(selected)
        current_location = selected[1]

    return ordered


# ---------------------------------------------------------------------------
# יצירת מצב התחלתי
# ---------------------------------------------------------------------------
def create_initial_state(
    start_location: dict,
    groups: list,
    max_capacity: int,
    available_time: float,
) -> dict:
    """יוצר מצב התחלתי עבור החיפוש."""
    return {
        "current_location": start_location,
        "current_time": 0.0,
        "remaining_groups": groups,
        "visited_groups": set(),
        "max_capacity": max_capacity,       # קיבולת רכב במנות
        "total_meals": 0,                    # סה"כ מנות מצטבר במסלול
        "route": [],
        "available_time": available_time,
    }


# ---------------------------------------------------------------------------
# בדיקת feasibility — האם אפשר לעבור לקבוצה נתונה?
# ---------------------------------------------------------------------------
def is_feasible(
    state: dict,
    group: dict,
    travel_time: float,
) -> bool:
    """
    בודק אם המעבר לקבוצה חוקי:
    1. לא חורג מהזמן הפנוי
    2. לא חורג מקיבולת המנות המצטברת של הרכב
    3. הקבוצה טרם בוקרה
    """
    service_time = get_group_service_time(group)
    group_meals = get_group_meals(group)
    group_families = get_group_families(group)

    # בדיקת זמן
    if state["current_time"] + travel_time + service_time > state["available_time"]:
        return False

    # בדיקה מצטברת של מנות — הרכב יכול לשאת עד max_capacity מנות בסה"כ
    if state["total_meals"] + group_meals > state["max_capacity"]:
        return False

    # בדיקה שהקבוצה לא בוקרה כבר
    if group["center_id"] in state["visited_groups"]:
        return False

    # בדיקה שיש נמענים בקבוצה
    if group_families == 0:
        return False

    return True


# ---------------------------------------------------------------------------
# החלת מעבר — יוצר מצב חדש אחרי הוספת קבוצה
# ---------------------------------------------------------------------------
def apply_move(state: dict, group: dict, travel_time: float) -> dict:
    """מחזיר מצב חדש אחרי הוספת הקבוצה למסלול."""
    families = get_group_families(group)
    group_meals = get_group_meals(group)
    service_time = get_group_service_time(group)

    ns = deepcopy(state)

    # עדכון מיקום — אחרי הנמען האחרון בקבוצה
    ordered_recipients = get_ordered_group_recipients(group, state["current_location"])
    if ordered_recipients:
        last_recipient = ordered_recipients[-1][1]
        ns["current_location"] = {
            "lat": last_recipient["lat"],
            "lng": last_recipient["lng"],
        }
    else:
        # fallback — מיקום המרכז
        ns["current_location"] = {
            "lat": group["center_lat"],
            "lng": group["center_lng"],
        }

    # עדכון זמן
    ns["current_time"] += travel_time + service_time

    # עדכון מסלול
    ns["route"] = ns["route"] + [group["center_id"]]
    ns["visited_groups"] = ns["visited_groups"] | {group["center_id"]}

    # עדכון מנות מצטבר
    ns["total_meals"] += group_meals

    # הסרת הקבוצה מהרשימה הנותרת
    ns["remaining_groups"] = [
        g for g in state["remaining_groups"]
        if g["center_id"] != group["center_id"]
    ]

    return ns


# ---------------------------------------------------------------------------
# מפתח ייחודי למצב עבור pruning
# ---------------------------------------------------------------------------
def state_key(state: dict) -> str:
    """
    מחזיר מפתח ייחודי למצב — בשימוש לגיזום במנוע החיפוש.
    מבוסס על קבוצת ה-visited_groups + מיקום נוכחי (מעוגל ל-4 ספרות).
    """
    visited = frozenset(state["visited_groups"])
    lat = state["current_location"]["lat"]
    lng = state["current_location"]["lng"]
    return f"{visited}|{round(lat, 4)}|{round(lng, 4)}"
