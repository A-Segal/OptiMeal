# אלגוריתם VRP — Grouped Delivery with Cumulative Meal Capacity

## הסבר מפורט

---

## 1. רקע — איפה האלגוריתם יושב במערכת

### האלגוריתם הראשון (Gale-Shapley) — רץ בלילה
- מקבל רשימת מרכזי חלוקה (suppliers) ונזקקים (consumers)
- משבץ נזקקים למרכזים לפי Match Score (מרחק, כמות מנות, טריות)
- מגבלה: כל מרכז מקבל עד 2 נזקקים
- ממלא טבלת `DeliveryAssignment` **בלי VolunteerID**
- זוהי שכבת השיבוץ המוקדם — מה יהיה מחר

### האלגוריתם השני (VRP) — רץ ביום החלוקה
- מתנדב מדווח על מיקום נוכחי וזמן פנוי (`VolunteerRequest`)
- האלגוריתם בונה לו מסלול של אילו קבוצות לקחת
- מעדכן `DeliveryAssignment.VolunteerID` לשיוך למתנדב

---

## 2. מודל הבעיה

### קלט
| פרמטר | מקור | תיאור |
|---|---|---|
| `start_location` | VolunteerRequest / כתובת | מיקום נוכחי של המתנדב |
| `available_time` | VolunteerRequest (שעות, למשל 2.5) | כמה זמן יש למתנדב |
| `vehicle_capacity` | Vehicle.capacity (1-5) → טבלת קיבולות | קיבולת הרכב **במנות** |

### טבלת קיבולות רכב (במנות)
| סוג רכב | קיבולת (מנות) | תיאור |
|---|---|---|
| 1 | 20 | אופנוע |
| 2 | 60 | Mini |
| 3 | 120 | פרטי |
| 4 | 250 | Station |
| 5 | 500 | מסחרי |

### קבוצות (Groups)
כל קבוצה = מרכז חלוקה + הנזקקים המשויכים אליו (בדרך כלל 1-2 נזקקים).
הקבוצות נלקחות מטבלת `DeliveryAssignment` — רק שורות ללא VolunteerID.

### הגבלות
1. **זמן**: `current_time + travel_time + service_time ≤ available_time`
   - `service_time = 5 דקות × מספר משפחות בקבוצה`
2. **קיבולת מנות מצטברת**: `total_meals + group_meals ≤ max_capacity`
   - **זו בדיקה מצטברת על כל המסלול** — הרכב יכול לשאת עד max_capacity מנות בסה"כ.
3. **ביקור חד-פעמי**: כל מרכז חלוקה נכנס למסלול פעם אחת, כל DeliveryAssignment פעם אחת.

### פלט
| שדה | תיאור |
|---|---|
| `route` | סדר center_id במסלול |
| `detailed_route` | מסלול מפורט ל-React: start → center → recipient → center → ... |
| `total_meals` | סה"כ מנות שהועברו במסלול |
| `final_time` | זמן כולל בדקות |
| `vehicle_capacity` | קיבולת הרכב במנות |
| `remaining_capacity` | קיבולת שנותרה = max_capacity - total_meals |

---

## 3. מבנה האלגוריתם — State Space Search

### מודל המצב (State)
כל מצב מייצג נקודה בתהליך החיפוש:

```python
{
    "current_location": {"lat": float, "lng": float},  # איפה המתנדב עכשיו
    "current_time": float,                              # זמן מצטבר (דקות)
    "remaining_groups": list,                           # קבוצות שעדיין לא בוצעו
    "visited_groups": set,                              # center_id של קבוצות במסלול
    "max_capacity": int,                                # קיבולת רכב במנות (לא משתנה)
    "total_meals": int,                                 # סה"כ מנות מצטבר במסלול
    "route": list,                                      # סדר center_id
    "available_time": float,                            # מגבלת זמן (לא משתנה)
}
```

**שימו לב**: `total_meals` מצטבר עם כל קבוצה שמתווספת. הקיבולת נבדקת באופן מצטבר:
"האם `total_meals + group_meals ≤ max_capacity`?"

### האלגוריתם
1. אתחול: `frontier = [initial_state]`, `best_seen = {}`
2. כל עוד frontier לא ריק:
   a. `new_frontier = []`
   b. לכל מצב s ב-frontier, לכל קבוצה g ב-s.remaining_groups:
      - חשב `travel_time = GoogleMaps(מיקום נוכחי, center_lat, center_lng)`
      - אם `travel_time == 999` — דלג (לא ניתן להגיע)
      - בדוק `is_feasible(s, g, travel_time)`:
        - זמן: `s.current_time + travel_time + service_time ≤ available_time`
        - **קיבולת: `s.total_meals + g.total_meals ≤ max_capacity`**
        - הקבוצה לא בוקרה
      - צור `ns = apply_move(s, g, travel_time)`:
        - `ns.total_meals = s.total_meals + g.total_meals`
        - `ns.current_time = s.current_time + travel_time + service_time`
        - `ns.current_location = מיקום הנמען האחרון`
        - `ns.route = s.route + [center_id]`
        - `ns.visited_groups = s.visited_groups | {center_id}`
        - `ns.remaining_groups = s.remaining_groups - {g}`
      - Pruning: אם `state_key(ns)` כבר נראה בזמן טוב יותר — דלג
      - הוסף ns ל-new_frontier
      - עדכן best_state אם ns יותר טוב
   c. `frontier = new_frontier`
3. החזר best_state

### קריטריון בחירת הפתרון הטוב ביותר
1. **מקסום total_meals** — כמה שיותר מנות
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
- 3 קבוצות: center 1 (120 מנות), center 2 (60 מנות), center 3 (80 מנות)
- קיבולת רכב: 250 מנות (Station)
- זמן: 180 דקות

האלגוריתם בודק את כל הסדרים האפשריים:
```
1 → 2 → 3: 120+60+80 = 260 מנות ❌ (חריגה מהקיבולת)
1 → 2:     120+60 = 180 מנות ✓ (40 דקות)
1 → 3:     120+80 = 200 מנות ✓ (35 דקות)
2 → 1:     60+120 = 180 מנות ✓ (45 דקות)
2 → 3:     60+80 = 140 מנות ✓ (42 דקות)
3 → 1:     80+120 = 200 מנות ✓ (38 דקות)
3 → 2:     80+60 = 140 מנות ✓ (40 דקות)
```

התוצאה: `1 → 3` (200 מנות, 35 דקות) — הכי הרבה מנות בזמן הקצר ביותר.

---

## 5. מבנה קבצים

```
services/vrp/
├── __init__.py
├── vrp_state.py     # מודל מצב, feasibility, פונקציות עזר
├── solver.py        # State Space Search — האלגוריתם הראשי
```

### `vrp_state.py`
- `VEHICLE_CAPACITY` — טבלת קיבולות במנות
- `get_vehicle_capacity(type)` — המרה סוג רכב → קיבולת במנות
- `get_group_families(group)` — מחזיר מספר משפחות בקבוצה
- `get_group_meals(group)` — מחזיר סך מנות בקבוצה
- `create_initial_state(...)` — יוצר מצב התחלתי (כולל total_meals=0)
- `is_feasible(state, group, travel_time)` — בודק חוקיות מעבר (בדיקה מצטברת של מנות)
- `apply_move(state, group, travel_time)` — יוצר מצב חדש אחרי מעבר
- `state_key(state)` — מפתח ייחודי למצב (לצורך pruning)

### `solver.py`
- `solve(groups, start_location, max_capacity, available_time, google_maps_service)`
- State Space Search מלא עם pruning
- מחזיר את המסלול האופטימלי (מקסום מנות)

---

## 6. איך להריץ

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
        {"step": 0, "type": "start", "action": "start", ...},
        {"step": 1, "type": "center", "action": "pickup", "center_id": 1, "meals": 120, ...},
        {"step": 2, "type": "recipient", "action": "deliver", "center_id": 1, "meals": 60, ...},
        ...
    ],
    "groups_count": 5,
    "vehicle_capacity": 250,
    "total_meals": 200,
    "final_time_minutes": 35.5,
    "visited_count": 3
}
```
