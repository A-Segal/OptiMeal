"""
VRP State Module — Grouped Delivery with Time Constraints

מייצג מצב בחיפוש, בדיקות feasibility, וחישובי קבוצות.
כל קבוצה = מרכז חלוקה + הנזקקים המשויכים אליו (1-2 נזקקים).
הקיבולת נבדקת לכל קבוצה בנפרד — אחרי שמסיימים קבוצה, הקיבולת מתפנה.
"""

import math

# ---------------------------------------------------------------------------
# קיבולות רכב — טבלה קבועה לפי סוג הרכב
# ---------------------------------------------------------------------------
VEHICLE_CAPACITY = {
    1: 1,   # אופנוע
    2: 3,   # Mini
    3: 6,   # Private
    4: 10,  # Station
    5: 20,  # Mischari
}

# זמן עיבוד פנימי של קבוצה (דקות) — איסוף מהמרכז + חלוקה לנזקקים
SERVICE_TIME_PER_FAMILY = 5  # דקות למשפחה


def get_vehicle_capacity(vehicle_type: int) -> int:
    """מחזיר קיבולת רכב (מספר משפחות מקסימלי לאיסוף) לפי סוג."""
    return VEHICLE_CAPACITY.get(vehicle_type, 3)


# ---------------------------------------------------------------------------
# עזר — חישוב משפחות בקבוצה
# ---------------------------------------------------------------------------
def get_group_families(group: dict) -> int:
    """
    מחזיר את מספר המשפחות בקבוצה.
    משתמש ב־group_families אם קיים, אחרת סופר recipients_locations.
    """
    if "group_families" in group and group["group_families"]:
        return group["group_families"]

    if "recipients_locations" in group:
        return len(group["recipients_locations"])

    return group.get("total_meals", 0)


def get_group_meals(group: dict) -> int:
    """מחזיר את מספר המנות הכולל בקבוצה."""
    return group.get("total_meals", 0)


def get_group_service_time(group: dict) -> float:
    """מחזיר את זמן השירות של הקבוצה בדקות."""
    return get_group_families(group) * SERVICE_TIME_PER_FAMILY


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Computes a simple haversine distance for recipient ordering."""
    radius = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def get_ordered_group_recipients(group: dict, from_location: dict | None = None) -> list[tuple]:
    """
    Orders recipients within a delivery group by proximity to the current location
    so the route visits addresses in a more realistic geographic sequence.
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
    """
    יוצר מצב התחלתי עבור החיפוש.
    """
    return {
        "current_location": start_location,
        "current_time": 0.0,
        "remaining_groups": groups,
        "visited_groups": set(),
        "max_capacity": max_capacity,
        "total_deliveries": 0,
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
    בודק האם המעבר לקבוצה הנתונה חוקי:
    1. זמן כולל (כולל שירות) לא חורג מהזמן הפנוי
    2. מספר המשפחות בקבוצה ≤ קיבולת הרכב
    3. הקבוצה עדיין לא בוצעה
    """
    families = get_group_families(group)

    # זמן שירות = זמן עיבוד לקבוצה
    service_time = get_group_service_time(group)

    new_time = state["current_time"] + travel_time + service_time

    # 1. מגבלת זמן
    if new_time > state["available_time"]:
        return False

    # 2. קיבולת — בדיקה לכל קבוצה בנפרד
    if families > state["max_capacity"]:
        return False

    # 3. הקבוצה לא בוצעה כבר
    if group["center_id"] in state["visited_groups"]:
        return False

    return True


# ---------------------------------------------------------------------------
# החלת מעבר — יוצר מצב חדש אחרי הוספת קבוצה
# ---------------------------------------------------------------------------
def apply_move(state: dict, group: dict, travel_time: float) -> dict:
    """
    מחזיר מצב חדש אחרי הוספת הקבוצה למסלול.
    """
    from copy import deepcopy

    families = get_group_families(group)
    service_time = get_group_service_time(group)

    ns = deepcopy(state)

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

    # עדכון deliveries
    ns["total_deliveries"] += families

    # הסרת הקבוצה מהרשימה הנותרת
    ns["remaining_groups"] = [
        g for g in state["remaining_groups"]
        if g["center_id"] != group["center_id"]
    ]

    return ns


# ---------------------------------------------------------------------------
# מפתח ייחודי למצב — עבור pruning
# ---------------------------------------------------------------------------
def state_key(state: dict) -> str:
    """
    מחזיר מפתח ייחודי למצב עבור pruning.
    מבוסס על סט הקבוצות שבוצעו והמיקום הנוכחי.
    """
    visited = frozenset(state["visited_groups"])
    loc = state["current_location"]
    # מעגל ל-4 ספרות כדי לקבץ מיקומים קרובים
    lat_key = round(loc["lat"], 4)
    lng_key = round(loc["lng"], 4)
    return f"{visited}|{lat_key}|{lng_key}"

