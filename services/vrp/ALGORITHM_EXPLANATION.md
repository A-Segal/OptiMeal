# אלגוריתם VRP — Grouped Delivery with Time Constraints

## הסבר מפורט

---

## 1. רקע — איפה האלגוריתם יושב במערכת

### האלגוריתם הראשון (Gale-Shapley) — רץ בלילה
- מקבל רשימת מרכזי חלוקה (suppliers) ונזקקים (consumers)
- משבץ נזקקים למרכזים לפי Match Score (מרחק, כמות מנות, טריות)
- מגבלה: כל מרכז מקבל עד 2 נזקקים
- ממלא את טבלת `DeliveryAssignment` — **בלי VolunteerID**
- זוהי שכבת השיבוץ המוקדם — מה יהיה מחר

### האלגוריתם השני (VRP) — רץ ביום החלוקה
- מתנדב מדווח על מיקום נוכחי וזמן פנוי (`VolunteerRequest`)
- האלגוריתם בונה לו מסלול של אילו קבוצות לקחת
- מעדכן `DeliveryAssignment.VolunteerID` לשיוך למתנדב
- **זה האלגוריתם שמימשתי עכשיו**

---

## 2. מודל הבעיה

### קלט
| פרמטר | מקור | תיאור |
|---|---|---|
| `start_location` | VolunteerRequest / Volunteer | מיקום התחלתי של המתנדב `{lat, lng}` |
| `available_time` | VolunteerRequest | זמן פנוי בשעות (למשל 2.5) — מומר לדקות |
| `vehicle_type` | Vehicle.capacity | סוג רכב: 1=אופנוע, 2=Mini, 3=Private, 4=Station, 5=Mischari |
| `max_capacity` | טבלת קיבולות | כמה משפחות הרכב יכול לשאת באיסוף אחד |
| `groups` | `build_groups()` | קבוצות משלוח — כל קבוצה = מרכז חלוקה + 1-2 נזקקים |

### טבלת קיבולות רכב
| type | שם | capacity (משפחות) |
|---|---|---|
| 1 | אופנוע | 1 |
| 2 | Mini | 3 |
| 3 | Private | 6 |
| 4 | Station | 10 |
| 5 | Mischari | 20 |

### אילוצים
1. **קיבולת**: `group_families ≤ max_capacity` — נבדק לכל קבוצה בנפרד, לא מצטבר. אחרי שמסיימים קבוצה — הקיבולת מתפנה.
2. **זמן**: `total_time ≤ available_time` — זמן כולל = זמן נסיעה (Google Maps) + זמן עיבוד (5 דקות למשפחה).
3. **מבנה קבוצה**: חייבים לסיים קבוצה לפני שעוברים לבאה. מסלול: `מרכז → נזקק/ים` (לא מרכז-מרכז).
4. **אין כפילויות**: כל קבוצה פעם אחת, כל DeliveryAssignment פעם אחת.

### פלט
| שדה | תיאור |
|---|---|
| `route` | סדר center_id במסלול |
| `detailed_route` | מסלול מפורט ל-React: start → center → recipient → center → ... |
| `total_deliveries` | מספר משפחות שהועברו |
| `final_time` | זמן כולל בדקות |

---

## 3. מבנה האלגוריתם — State Space Search

### מודל המצב (State)
כל מצב מייצג נקודה בתהליך החיפוש:

```python
{
    "current_location": {"lat": float, "lng": float},  # איפה המתנדב עכשיו
    "current_time": float,                              # זמן מצטבר (דקות)
    "remaining_groups": list,                            # קבוצות שעדיין לא בוצעו
    "visited_groups": set,                               # center_id של קבוצות במסלול
    "max_capacity": int,                                 # קיבולת רכב (לא משתנה)
    "total_deliveries": int,                             # סה"כ משפחות במסלול
    "route": list,                                       # סדר center_id
    "available_time": float,                             # מגבלת זמן (לא משתנה)
}
```

**שימו לב**: אין `capacity_left` — הקיבולת לא מצטברת! היא נבדקת לכל קבוצה בנפרד: "האם `group_families ≤ max_capacity`?".

### תהליך החיפוש

```
1. התחלה:
   - מצב התחלתי: מיקום המתנדב, זמן 0, כל הקבוצות זמינות
   - best_state = מצב התחלתי
   - frontier = [מצב התחלתי]

2. כל עוד frontier לא ריק:
   a. new_frontier = []
   b. לכל מצב s ב-frontier:
      i.   לכל קבוצה g שנותרה ב-s.remaining_groups:
           - חשב travel_time = GoogleMaps(מיקום נוכחי → מרכז הקבוצה)
           - אם travel_time == None/999 → דלג
           - בדוק feasibility:
             · time = current_time + travel_time + (5 × group_families)
             · time ≤ available_time?
             · group_families ≤ max_capacity?
             · group לא בוצעה כבר?
           - אם לא feasible → דלג
           - צור מצב חדש ns:
             · ns.current_time = s.current_time + travel_time + service_time
             · ns.current_location = מיקום הנזקק האחרון בקבוצה
             · ns.route = s.route + [center_id]
             · ns.visited_groups = s.visited_groups ∪ {center_id}
             · ns.total_deliveries = s.total_deliveries + group_families
             · ns.remaining_groups = s.remaining_groups − {group}
           - Pruning: דלג אם כבר ראינו מצב דומה בזמן טוב יותר
           - הוסף ns ל-new_frontier
           - עדכן best_state אם ns יותר טוב
   c. frontier = new_frontier

3. החזר best_state
```

### קריטריון בחירת הפתרון הטוב ביותר
1. **מקסום deliveries** — כמה שיותר משפחות
2. **במקרה של שוויון** — מינימום זמן כולל

### Pruning (גיזום)
שומרים `best_seen[state_key] = best_time`.

`state_key` מורכב מ:
- `frozenset(visited_groups)` — אילו קבוצות בוצעו
- `round(current_lat, 4)` + `round(current_lng, 4)` — מיקום נוכחי מקורב

אם הגענו לאותו סט קבוצות באותו מיקום (בערך) **בזמן גרוע יותר** — אין טעם להמשיך מהמצב הזה, מדלגים.

---

## 4. דוגמה לריצה

נתון:
- 3 קבוצות: center 1 (2 families), center 2 (3 families), center 3 (1 family)
- קיבולת: 6
- זמן: 120 דקות

האלגוריתם בודק את כל הסדרים האפשריים:
```
1 → 2 → 3  ✓ (2+3+1=6 families, 24 min)
1 → 3 → 2  ✓ (2+1+3=6 families, 28 min)
2 → 1 → 3  ✓ (3+2+1=6 families, 30 min)
2 → 3 → 1  ✓ (3+1+2=6 families, 32 min)
...
```
בוחר `1 → 2 → 3` — הכי מהיר (24 דקות).

---

## 5. דוגמה עם מגבלת זמן

נתון:
- 3 קבוצות, אבל center 2 רחוק (~50 ק"מ)
- זמן: 10 דקות בלבד

האלגוריתם בודק:
```
1 → 3  ✓ (2 families, 6 min)
1 → 2  ✗ (זמן נסיעה > 10 דקות)
```
בוחר `1` — הקבוצה היחידה שאפשרית בזמן הנתון.

---

## 6. סיבוכיות

- **זמן**: O(n!) במקרה הגרוע (כל הסדרים של n קבוצות)
- **בפועל**: pruning מפחית משמעותית. עם 10-15 קבוצות — עובד מהר.
- **Google Maps**: N×(N-1) קריאות API (מטריצת מרחקים מלאה בין קבוצות + start). הקריאות מתבצעות תוך כדי החיפוש, לא מראש. לשיפור עתידי — אפשר להוסיף cache או async.

---

## 7. מבנה קבצים

```
services/vrp/
├── __init__.py
├── vrp_state.py       # מודל מצב, feasibility, פונקציות עזר
├── solver.py          # State Space Search — האלגוריתם הראשי
```

### `vrp_state.py`
- `VEHICLE_CAPACITY` — טבלת קיבולות
- `get_vehicle_capacity(type)` — המרה סוג רכב → קיבולת
- `get_group_families(group)` — מחזיר מספר משפחות בקבוצה
- `create_initial_state(...)` — יוצר מצב התחלתי
- `is_feasible(state, group, travel_time)` — בודק חוקיות מעבר
- `apply_move(state, group, travel_time)` — יוצר מצב חדש אחרי מעבר
- `state_key(state)` — מפתח ייחודי למצב (לצורך pruning)

### `solver.py`
- `solve(groups, start_location, max_capacity, available_time, google_maps_service)`
- State Space Search מלא עם pruning
- מחזיר את המסלול האופטימלי

---

## 8. איך להריץ

### Postman
```
POST http://127.0.0.1:5000/volunteer_request/run_route/2
Headers: Content-Type: application/json
Body:
{
    "address": "רחוב חזון איש 5, בני ברק",
    "available_time": 2.5
}
```

### תשובה
```json
{
    "volunteer_id": 2,
    "start_location": {"lat": 32.0853, "lng": 34.7818},
    "route": [1, 3, 2],
    "detailed_route": [
        {"step": 0, "type": "start", ...},
        {"step": 1, "type": "center", "center_id": 1, ...},
        {"step": 2, "type": "recipient", "assignment_id": 101, ...},
        {"step": 3, "type": "center", "center_id": 3, ...},
        ...
    ],
    "groups_count": 5,
    "vehicle_capacity": 6,
    "total_meals": 4,
    "visited_count": 3
}
```
