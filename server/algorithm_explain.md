# SmartPath Algorithm Documentation — Detailed Explanation

מסמך זה מסביר לעומק את שני האלגוריתמים המרכזיים במערכת.

---

## Algorithm 1 — Batch Matching (Gale-Shapley Style)

### מטרה
לשבץ מוטבים למרכזי חלוקה באופן אופטימלי — כל מוטב לקבל אוכל ממרכז החלוקה המתאים לו ביותר.

### קובצי קוד מעורבים

| קובץ | תפקיד |
|------|-------|
| `services/batch_algoritm/matching_algorithm.py` | בניית מועמדים, ניקוד, מיון |
| `services/batch_algoritm/main_algoritm.py` | לוגיקת השיבוץ — Gale-Shapley |
| `services/batch_algoritm/execute_full_matching.py` | Wrapper להרצה + print |
| `services/delivery_assignment_service.py` | שמירת תוצאות ל-DB |

### איך זה עובד

#### שלב 0 — הכנת נתונים

```
for each center:
    get center's DC_Request → amount_of_meals, freshness_priority

for each recipient:
    get recipient's Recipient_Request → amount_of_meals

for each (center, recipient) pair:
    if center_meals <= 0 → skip
    if recipient_meals <= 0 → skip
    distance = haversine(center.location, recipient.location)
    if distance > 100km → skip
    
    meal_type = 1  // חם, 0 = יבש
    if meal_type == 1:
        score = distance_ratio * 0.95 + meals_ratio * 0.05 + distance_ratio * 0.15
    else:
        score = distance_ratio * 0.8 + meals_ratio * 0.2 + distance_ratio * 0.04
    // איפה:
    //   distance_ratio = distance / 100
    //   meals_ratio = (center_meals - recipient_meals) / center_meals
    // ציון נמוך = יותר טוב
```

הניקוד משלב שלושה שיקולים:
- **מרחק (80%)** — ככל שקרוב יותר, ציון טוב יותר
- **ניצול מזון (20%)** — ככל שנשאר יותר אוכל אחרי ההקצאה, ציון טוב יותר
- **סוג ארוחה** — ארוחה חמה מקבלת דחיפה לקרבה גבוהה יותר, כדי לצמצם זמן הגעה

#### שלב 1 — שיבוץ ראשי (Gale-Shapley)

```
candidates_by_center = sort_center_candidates(candidates)  // מיון עולה לפי score

queue = deque(כל ה-centers)
recipient_assignment = {}    // recipient_id → {center_id, score, recipient_meals, ...}
current_index = {center: 0}  // איזה מועמד כל center מנסה עכשיו

while queue לא ריק AND לא שובצו כל המוטבים:
    center = queue.popleft()
    idx = current_index[center]
    
    if idx >= len(candidates[center]):  // נגמרו המועמדים ל-center הזה
        continue
    
    recipient, score, recipient_meals, center_meals = candidates[center][idx]
    
    if recipient not in recipient_assignment:
        // שיבוץ חופשי
        recipient_assignment[recipient] = {center, score, recipient_meals, ...}
        current_index[center] += 1
        queue.append(center)  // חוזר לתור עם המועמד הבא
        
    else:
        old_center = recipient_assignment[recipient]["center_id"]
        old_score = recipient_assignment[recipient]["score"]
        
        if score < old_score:  // ההתאמה החדשה טובה יותר
            // מחליפים
            recipient_assignment[recipient] = {center, score, ...}
            current_index[center] += 1
            queue.append(center)     // center ממשיך למועמד הבא
            queue.append(old_center) // old_center חוזר לתור (צריך למצוא מוטב אחר)
        else:
            // ההתאמה הישנה טובה יותר — center מנסה את המועמד הבא
            current_index[center] += 1
            queue.append(center)
```

זהו מימוש של **Deferred Acceptance** (Gale-Shapley) — מרכזי חלוקה "מציעים" למוטבים לפי סדר ההעדפות. מוטב "מקבל" את ההצעה הטובה ביותר, אבל יכול להתחלף אם מגיעה הצעה טובה יותר. מרכז שנדחה חוזר לתור ומציע למוטב הבא ברשימה.

#### שלב 2 — השלמת קיבולת

```
unassigned = כל ה-recipients שלא שובצו

center_usage = {
    center_id: {first_recipient, used_meals}  // סיכום שלב 1
}

remaining_meals_by_center = {
    center_id: original_meals - used_meals
}

// בונים מועמדים חדשים — רק למוטבים שלא שובצו
// והמרחק נמדד מה-first_recipient של ה-center (לא מהמרכז עצמו)
// ומגבלת מרחק 10km
second_phase = build_second_phase_candidates(...)

// חישוב score לשלב 2:
remaining_ratio = (remaining_meals - recipient_meals) / remaining_meals
score = (distance / 100) * 0.8   +   (1 - remaining_ratio) * 0.2

אותו Gale-Shapley כמו שלב 1, אבל:
- רק מוטבים לא משובצים
- מועמדים מבוססי remaining_meals (לא center_meals המקורי)
- מרחק מחושב מ-first_recipient
- max_distance = 10km (לא 100)
```

### מגבלות/הנחות
- **משתמש ב-Haversine** (קו אווירי), לא בזמני נסיעה אמיתיים של Google Maps
- **מגבלת 100km לשלב 1** — זוגות רחוקים מדי לא ייחשבו בכלל
- **מגבלת 10km לשלב 2** — טווח מצומצם מאוד לסבב שני
- **אין חפיפה** — כל מוטב משויך למרכז אחד בלבד
- **Freshness priority** — משומר ב-assignment אבל **לא משפיע על הניקוד**, רק נשמר כשדה

---

## Algorithm 2 — VRP Route Solver

### מטרה
בהינתן קבוצות (groups) של משלוחים שכבר שובצו למרכזי חלוקה, למצוא את המסלול האופטימלי למתנדב — מקסום מספר מוטבים, מינימום זמן.

### קובצי קוד מעורבים

| קובץ | תפקיד |
|------|-------|
| `services/volunteer_route_service.py` | שכבת service — הכנה והרצה |
| `services/vrp/solver.py` | State Space Search — חיפוש המסלול |
| `services/vrp/vrp_state.py` | מצב (state), בדיקות feasibility, פונקציות עזר |
| `services/utils/googleMaps.py` | Google Maps API — מרחקים וזמנים אמיתיים |
| `repository/delivery_assignmentRepository.py` | `build_groups()` — איסוף הנתונים מה-DB |

### איך זה עובד

#### שלב 1 — איסוף נתונים (בתוך `run_volunteer_route`)

```
volunteer = volunteer_repo.get_volunteer(volunteer_id)
vehicle = volunteer.vehicle
vehicle_type = vehicle.capacity  // 1-5
vehicle_capacity = VEHICLE_CAPACITY[vehicle_type]

if start_address:      → geocode → start_location
if start_location_param → start_location = param

groups = assignment_repo.build_groups()  // קבוצות שלא שובץ להן מתנדב
// filter: רק groups עם center_id, center_lat, center_lng תקינים

available_time_minutes = available_time * 60  // או 999999 אם אין הגבלה
```

#### שלב 2 — build_groups() (איך נראית קבוצה)

```python
group = {
    "center_id": 5,
    "center_lat": 32.0853,
    "center_lng": 34.7818,
    "recipients_locations": [
        {"lat": 32.0900, "lng": 34.7900},
        {"lat": 32.0800, "lng": 34.7750}
    ],
    "assignment_ids": [101, 102],
    "meal_types": [1, 0],
    "total_meals": 4,
    "group_families": 2
}
```

#### שלב 3 — State Space Search (ליבת האלגוריתם)

**הגדרת מצב (State):**
```python
state = {
    "current_location": {lat, lng},    // איפה המתנדב עכשיו
    "current_time": 0.0,              // זמן מצטבר בדקות
    "remaining_groups": [...],         // קבוצות שעוד לא ביקרו בהן
    "visited_groups": set(),           // קבוצות שכבר ביקרו
    "max_capacity": 6,                 // קיבולת רכב (משפחות)
    "total_deliveries": 0,            // סך משפחות שקיבלו משלוח
    "route": [],                       // סדר הקבוצות במסלול
    "available_time": 480              // מגבלת זמן כוללת (דקות)
}
```

**בדיקת feasibility — `is_feasible(state, group, travel_time)`:**
```
1. families_in_group = group_families(group)    // ממפתח "group_families"
2. if families_in_group > max_capacity → False  // חריגה מקיבולת
3. service_time = families * 5 דקות
4. total = current_time + travel_time + service_time
5. if total > available_time → False           // חריגה מזמן
6. return True
```

**חיפוש — BFS עם pruning:**

```
create_initial_state(start_location, groups, capacity, available_time)
frontier = [initial_state]
best_state = initial_state
best_seen = {}   // state_key → best_time_achieved
iteration = 0

while frontier לא ריק AND iteration < 50:
    new_frontier = []
    
    for state in frontier:
        for group in state.remaining_groups:
            travel_time = travel_time_between_points(
                state.current_location,
                group.center_location
            )
            
            if not is_feasible(state, group, travel_time):
                continue
            
            new_state = apply_move(state, group, travel_time)
            
            // Pruning: דלג אם הגענו למצב דומה בזמן טוב יותר
            key = state_key(new_state)
            if key in best_seen and best_seen[key] <= new_state.current_time:
                continue
            best_seen[key] = new_state.current_time
            
            new_frontier.append(new_state)
            
            // עדכן best_state
            if new_state.total_deliveries > best_state.total_deliveries OR
               (equal deliveries AND new_state.current_time < best_state.current_time):
                best_state = new_state
    
    // מיון: קח עד 3 מצבים הכי טובים (Branch & Bound)
    new_frontier.sort(key=lambda s: (-s["total_deliveries"], s["current_time"]))
    frontier = new_frontier[:3]
    iteration += 1

return best_state
```

**apply_move — מה קורה כשמוסיפים קבוצה למסלול:**
```
1. service_time = group_families * 5 דקות
2. new_location = המיקום של המוטב האחרון בקבוצה
    (אם יש מוטבים: המיקום האחרון ב-ordered_recipients
    אחרת: מיקום מרכז החלוקה)
3. new_time = old_time + travel_time + service_time
4. new_route = old_route + [center_id]
5. new_remaining = old_remaining - {this_group}
6. total_deliveries += group_families
```

#### שלב 4 — סדר מוטבים בתוך קבוצה (Nearest Neighbor)

```
get_ordered_group_recipients(group, current_location):
    pairs = list(zip(assignment_ids, recipients_locations))
    ordered = []
    cursor = current_location (או center_location כברירת מחדל)
    
    while pairs לא ריק:
        next = ה-recipient הכי קרוב ל-cursor (Haversine)
        ordered.append(next)
        cursor = next.location
        remove next from pairs
    
    return ordered
```

#### שלב 5 — travel_time_between_points (Google Maps)

```python
def travel_time_between_points(lat1, lng1, lat2, lng2):
    # מנרמל ל-4 ספרות עשרוניות (דיוק של ~11 מטר)
    key = (round(lat1,4), round(lng1,4), round(lat2,4), round(lng2,4))
    
    # בדוק גם הפוך (דו-כיווני)
    reverse_key = (key[2], key[3], key[0], key[1])
    
    if key in cache: return cache[key]
    if reverse_key in cache: return cache[reverse_key]
    
    # קריאה ל-Google Distance Matrix API
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?..."
    response = requests.get(url)
    
    if status != 'OK' or element_status != 'OK':
        cache[key] = 999999
        return 999999
    
    minutes = duration_seconds / 60
    cache[key] = minutes
    return minutes
```

**הערה:** הפונקציה מחזירה `999999` במקרה של שגיאה — מה שהופך את המסלול לבלתי אפשרי (feasibility check ייכשל). זוהי התנהגות **נכונה**.

### מגבלות/הנחות
- **מקסימום 50 איטרציות** — החיפוש מוגבל ל-50 סבבים
- **Branch & Bound:** עד 3 מצבים הכי טובים נשמרים בכל איטרציה (לא חיפוש מלא — tradeoff של דיוק מול ביצועים)
- **קיבולת לקבוצה** — הקיבולת נבדקת פר-קבוצה. אחרי שמסיימים קבוצה, הקיבולת "מתאפסת" לקבוצה הבאה
- **זמן שירות:** 5 דקות למשפחה, קבוע
- **Google Maps cache:** מנורמל ל-4 ספרות עשרוניות, cache in-memory
- **state_key:** ממיין את ה-visited_groups ומגביל ל-4 תווים — לא ייחודי לחלוטין, pruning עלול להיות אגרסיבי מדי
- **Haversine למיון פנימי:** סדר המוטבים בתוך קבוצה משתמש במרחק אווירי, לא בזמן נסיעה אמיתי
- **האלגוריתם חמדן (greedy) במובן מסוים:** בגלל ה-Branch & Bound (רק 3 מצבים לאיטרציה), ייתכן שהפתרון הגלובלי האופטימלי לא יימצא. זה tradeoff מכוון לטובת ביצועים

---

## איך האלגוריתמים משתלבים יחד

```
┌─────────────────────────────────────────────────────────────────┐
│                         תהליך מלא                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. centers + recipients  ←  נתונים מה-DB                      │
│            │                                                    │
│            ▼                                                    │
│  2. Algorithm 1: Batch Matching                                │
│     • Gale-Shapley דו-שלבי                                     │
│     • פלט: recipient → center (איזה מוטב מקבל מאיפה)           │
│            │                                                    │
│            ▼                                                    │
│  3. שמירה ב-DeliveryAssignment                                 │
│     • כל שיבוץ הופך ל-DeliveryAssignment                       │
│     • VolunteerID = NULL (עדיין אין מתנדב)                     │
│            │                                                    │
│            ▼                                                    │
│  4. בקשה של מתנדב: POST /volunteer_request/run_route/{id}      │
│            │                                                    │
│            ▼                                                    │
│  5. build_groups() ← DeliveryAssignment WHERE VolunteerID=NULL  │
│     • מקבץ assignments לפי DistributionCenterID                │
│            │                                                    │
│            ▼                                                    │
│  6. Algorithm 2: VRP Route Solver                              │
│     • State Space Search                                       │
│     • Google Maps Distance Matrix API                          │
│     • פלט: route = [center_id_1, center_id_2, ...]            │
│            │                                                    │
│            ▼                                                    │
│  7. assign_volunteer_to_group()                                │
│     • מעדכן VolunteerID ב-DeliveryAssignment                  │
│                                                                 │
│  8. פלט ל-Frontend:                                            │
│     • detailed_route (step-by-step עם נ"צ)                    │
│     • total_deliveries, final_time_minutes                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Detail: build_groups()

השאילתה ב-`DeliveryAssignmentRepository.build_groups()`:
```sql
SELECT * FROM DeliveryAssignment
WHERE VolunteerID IS NULL
```

ואז:
1. אוספת את כל ה-`DistributionCenterID` וה-`RecipientID` הייחודיים
2. שולפת את האובייקטים המלאים מ-`DistributionCenter` ומ-`Recipient` (preload — מונע N+1)
3. מקבצת לפי `DistributionCenterID`:
   - `center_lat`, `center_lng` — מ-DistributionCenter
   - `recipients_locations` — מערך של `{lat, lng}` מ-Recipient
   - `assignment_ids` — מערך של DeliveryAssignment.id
   - `total_meals` — סכום amount_of_meals
    - `group_families` — ספירת מוטבים בקבוצה

---

## Vehicle Capacity Table

| capacity (DB) | סוג רכב | משפחות לקבוצה |
|---------------|---------|---------------|
| 1 | אופנוע | 1 |
| 2 | Mini | 3 |
| 3 | Private | 6 |
| 4 | Station | 10 |
| 5 | מסחרי | 20 |

---

## Performance Characteristics

### Algorithm 1 (Batch Matching)
- **Complexity:** O(C × R) to build candidates + O(queue_ops) for Gale-Shapley
- **Bottleneck:** `build_candidates_for_centers` — nested loop over all centers × recipients (Haversine each pair)
- **Google Maps:** Not used — Haversine only

### Algorithm 2 (VRP) — Correction: Full Exhaustive Search

I previously stated the solver has a 50-iteration cap and 3-state branch limit. **This was wrong.** Looking at the actual source:

- **No iteration counter** — `while frontier:` runs until the queue is empty (all reachable states expanded)
- **No branch limit** — every feasible new state is appended to `new_frontier` unconditionally. No sort, no truncation
- **Pruning only by `state_key`** — skips duplicate states: same visited-groups set + same rounded (4 decimal) location, if we've already reached that state with a better or equal time

**Complexity:** Worst case O(N!) for N groups, but in practice heavily pruned by `state_key` (location rounded to 4 decimals ~11m precision). Google Maps caching eliminates redundant API calls. For sparse geographic distribution, this runs quickly even with many groups.

---

*Last updated: July 2026 | Project: SmartPath Server*
