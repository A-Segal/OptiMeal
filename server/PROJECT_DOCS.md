# SmartPath — Project Documentation & Instruction Page

## 📋 What This Project Does

SmartPath is a **food delivery management system**. It connects three types of users:

| User Type | Role |
|-----------|------|
| **Distribution Centers** | Provide meals to deliver |
| **Recipients** | Receive meal deliveries |
| **Volunteers** | Drive and deliver meals from centers to recipients |

The system has two smart algorithms:
1. **Batch Matching** — Automatically matches recipients to get food from distribution centers (Gale-Shapley style)
2. **VRP Route Solver** — Calculates the best delivery route for each volunteer (State Space Search with pruning)

---

## 🛠 Tech Stack

| Layer | What We Use |
|-------|-------------|
| Language | Python 3 |
| Web Framework | Flask |
| Database | Microsoft SQL Server (`deliveryDB`) |
| ORM | SQLAlchemy + pyodbc |
| Maps | Google Maps API (Geocoding + Distance Matrix) |
| Frontend | React (separate project — `@react-google-maps/api`, `axios`) |

---

## 📁 Project File Structure

```
smartpath-project/
│
├── main.py                          # Entry point — starts Flask server
├── db_connection.py                 # Database connection (SQLAlchemy + SQL Server)
├── package.json                     # Frontend JavaScript dependencies
│
├── controller/                      # API endpoints (Flask Blueprints)
│   ├── auth_controller.py           # Login endpoint
│   ├── volunteer_controller.py      # Volunteer CRUD
│   ├── recipient_controller.py      # Recipient CRUD
│   ├── recipient_request_controller.py
│   ├── dc_request_controller.py
│   ├── permission_controller.py
│   ├── vehicle_controller.py
│   ├── staff_member_controller.py
│   ├── distribution_center_controller.py
│   ├── delivery_assignment_controller.py
│   └── volunteer_request_controller.py  # ← VRP route endpoint here
│
├── models/                          # SQLAlchemy ORM models
│   ├── base.py                      # Base = declarative_base()
│   ├── volunteer.py                 # Volunteer table
│   ├── recipient.py                 # Recipient table
│   ├── distribution_center.py       # DistributionCenter table
│   ├── delivery_assignment.py       # DeliveryAssignment table
│   ├── DC_request.py               # DC_Request table
│   ├── recipient_request.py        # Recipient_Request table
│   ├── volunteer_request.py        # volunteer_request table
│   ├── vehicle.py                  # Vehicle table
│   ├── staff_member.py             # StaffMember table
│   └── permission.py               # Permission table
│
├── repository/                      # Database access layer (CRUD operations)
│   ├── VolunteerRepository.py
│   ├── RecipientRepository.py
│   ├── DistributionCenterRepository.py
│   ├── DeliveryAssignmentRepository.py  # ← build_groups() for VRP here
│   ├── DCRequestRepository.py
│   ├── RecipientRequestRepository.py
│   ├── VolunteerRequestRepository.py
│   ├── VehicleRepository.py
│   ├── StaffMemberRepository.py
│   └── PermissionRepository.py
│
├── dto/                             # Data Transfer Objects (JSON serialization)
│   └── ... (10 DTO files)
│
├── services/                        # Business logic
│   ├── delivery_assignment_service.py  # Runs matching → saves to DB
│   ├── volunteer_route_service.py      # Runs VRP routing → saves to DB
│   ├── utils/
│   │   └── googleMaps.py              # Google Maps API functions
│   ├── batch_algoritm/
│   │   ├── main_algoritm.py            # Two-phase Gale-Shapley matching
│   │   ├── matching_algorithm.py       # Scoring & candidate building
│   │   ├── execute_full_matching.py    # Wrapper
│   │   └── print_results.py           # Debug output
│   └── vrp/
│       ├── solver.py                  # State Space Search VRP solver (active)
│       ├── vrp_state.py               # State + feasibility checks
│       ├── engine.py                  # ⚠️ OLD — not used anymore
│       └── state.py                   # ⚠️ OLD — not used anymore
│
├── csvfiles/                        # Test data
├── tests/
│   └── test_repository.py           # Manual integration test
├── PROJECT_DOCS.md                  # ← THIS FILE
└── algorithm_explain.md             # Detailed algorithm explanation
```

---

## 🗄 Database Tables

| Table | Key Columns |
|-------|------------|
| **Volunteer** | id, fname, lname, username, password, mail, phone |
| **Recipient** | id, fname, lname, username, password, mail, phone, location_lat, location_lng |
| **DistributionCenter** | id, fname, lname, username, password, mail, phone, location_lat, location_lng |
| **Recipient_Request** | RecipientID, amount_of_meals |
| **DC_Request** | DistributionCenterID, amount_of_meals, freshness_priority |
| **DeliveryAssignment** | id, DistributionCenterID, RecipientID, VolunteerID, amount_of_meals, freshness_priority |
| **volunteer_request** | id, volunteer_id, location_lat, location_lng, available_time |
| **Vehicle** | id, VolunteerID, capacity (1=motorcycle, 2=Mini, 3=Private, 4=Station, 5=Commercial) |
| **StaffMember** | id, fname, lname, username, password, mail, phone, PermissionID |
| **Permission** | id, type |

---

## 🌐 API Endpoints (53 Total)

Every entity has 5 standard endpoints: `GET /<entity>`, `GET /<entity>/<id>`, `POST /<entity>`, `PUT /<entity>/<id>`, `DELETE /<entity>/<id>`.

### Special Endpoints

| Method | Endpoint | What It Does |
|--------|----------|-------------|
| `POST` | `/auth/login` | Login — checks username/password against Volunteer → Recipient → DistributionCenter |
| `POST` | `/delivery_assignment/run_matching` | Runs batch matching algorithm & creates assignments |
| `POST` | `/volunteer_request/run_route/<volunteer_id>` | Runs VRP route optimization for one volunteer |
| `DELETE` | `/vehicles/volunteer/<volunteer_id>` | Deletes all vehicles belonging to a volunteer |

### All Entity Endpoints

| Entity | Base URL |
|--------|----------|
| Volunteers | `/volunteers` |
| Recipients | `/recipients` |
| Recipient Requests | `/recipient_request` |
| DC Requests | `/dc_requests` |
| Permissions | `/permissions` |
| Vehicles | `/vehicles` |
| Staff Members | `/staff` |
| Distribution Centers | `/distribution_center` |
| Delivery Assignments | `/delivery_assignment` |
| Volunteer Requests | `/volunteer_request` |

---

## 🧠 How the Algorithms Work

For a detailed explanation of both algorithms with pseudocode, see [algorithm_explain.md](algorithm_explain.md).

### Algorithm 1 — Batch Matching (Gale-Shapley style)

**Entry point:** `services/batch_algoritm/main_algoritm.py` → `run_full_matching(db)`

**Phase 1 (Main matching):**
1. Build candidates: every center gets a sorted list of (recipient, score) pairs
2. Score formula: `score = (distance/100) * 0.8 + ((center_meals - recipient_meals)/center_meals) * 0.2` — lower is better
3. Centers propose to recipients in order of best score. If a recipient is already assigned, the better-scored center "wins" and the old center goes back to the queue (Gale-Shapley deferred acceptance)
4. Max initial distance: 100km

**Phase 2 (Fill remaining capacity):**
- Unassigned recipients get matched to centers that still have meals left
- Limited to 10km from the center's first assigned recipient
- Different score formula accounting for remaining meals

### Algorithm 2 — VRP Route Solver

**Entry point:** `services/volunteer_route_service.py` → `run_volunteer_route()`

The solver uses **State Space Search** (full BFS with pruning):

1. **Input:** Groups of unassigned deliveries, volunteer start location, vehicle capacity, available time
2. **State:** Current location, current time, remaining groups, visited groups, total deliveries, route
3. **Search:** Each iteration expands all remaining groups as candidates. For each — check feasibility (time + capacity per group), apply move, check pruning (skip states already seen at this visited-set + rounded-location with better or equal time)
4. **Goal:** Maximize number of deliveries (families). Tiebreaker: minimum total time
5. **Exhaustive:** No iteration cap, no branch limit — the search explores the full state space reachable under pruning. Worst case O(N!) but pruning is aggressive in practice
6. **Google Maps:** Real travel times via Distance Matrix API, with in-memory cache, Haversine-based neighbor sort
7. **Capacity:** Per-group capacity check — families per group must not exceed vehicle capacity. Vehicle capacities: 1=1, 2=3, 3=6, 4=10, 5=20 families
8. **Service time:** 5 minutes per family at each group
9. **Route ordering within group:** Nearest-neighbor heuristic — recipients visited in order of proximity from current location

---

## 🐛 Known Bugs & Issues

### 🔴 CRITICAL — Must Fix

| # | Problem | Where | What Happens |
|---|---------|-------|-------------|
| 1 | Google API key hardcoded in source | `services/utils/googleMaps.py:6` | `AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY` is in source code — security risk, visible in git, can't rotate without code change (has env var fallback but default is hardcoded) |

### 🟠 HIGH — Security & Design

| # | Problem | Where | What Happens |
|---|---------|-------|-------------|
| 2 | Plaintext passwords in DB | `controller/auth_controller.py` | Passwords stored and compared as plaintext — no hashing |
| 3 | No authentication token/JWT/session | All controllers | API is completely open — anyone can call any endpoint |
| 4 | Separate DB session in matching | `services/batch_algoritm/execute_full_matching.py` | `execute_full_matching()` opens a separate DB session for the algorithm — data inconsistency risk |
| 5 | Duplicate imports | `db_connection.py:10-15` | `Permission`, `Vehicle`, `Volunteer` imported twice — messy but harmless |
| 6 | 187 lines commented-out duplicate code | `services/volunteer_route_service.py:179-366` | Nearly entire service duplicated and commented out at bottom of file |
| 7 | Commented-out duplicate endpoint | `controller/volunteer_request_controller.py:163-181` | Old version of `run_route` endpoint left commented out |

### 🟡 MEDIUM — Functionality Issues

| # | Problem | Where | What Happens |
|---|---------|-------|-------------|
| 8 | Legacy dead code files | `services/vrp/engine.py`, `services/vrp/state.py` | Old VRP engine using class-based groups. Never imported — just adds confusion |
| 9 | No database migrations | `db_connection.py:23` | `create_all()` runs on import. No Alembic. Schema changes need manual SQL |
| 10 | No input validation | All controllers | Bad data → unhandled SQLAlchemy errors → 500 crashes instead of helpful error messages |
| 11 | No JSON error handler | `main.py` | Uncaught exceptions return HTML 500 page, not JSON. API clients get garbage |
| 12 | Inconsistent table naming | `models/volunteer_request.py` | Table is `volunteer_request` (lowercase) but all others are PascalCase. FK is `volunteer_id` but others are `VolunteerID` |
| 13 | No logging — only `print()` | Whole project | Debug messages go to console with no levels, no file output, no way to disable |
| 14 | VRP solver compressed in repo | `services/vrp/solver.py` | File appears to have been minified/compressed — all comments, docstrings, and whitespace stripped. Very hard to read and maintain |

### 🔵 LOW — Code Quality

| # | Problem | Where |
|---|---------|-------|
| 15 | `execute_full_matching` prints instead of returning structured result | `services/batch_algoritm/execute_full_matching.py` |
| 16 | `try/finally` used without `except` in several places | Various controllers |
| 17 | `create_all()` called at import time, not startup | `main.py:37` |
| 18 | No `.env` file support — config mixed with code | Various |
| 19 | Debug prints in production code | `services/vrp/solver.py`, `services/utils/googleMaps.py` |
| 20 | Hebrew text direction mismatch (LTR in RTL comments) | `services/vrp/vrp_state.py` and others — mixed direction makes code hard to read in some editors |

---

## 🚀 How to Run

### Prerequisites
- Python 3 installed
- Microsoft SQL Server running locally
- `deliveryDB` database created
- ODBC Driver 17 for SQL Server installed

### Steps
```bash
# 1. Install Python dependencies
pip install flask flask-cors sqlalchemy pyodbc requests

# 2. Run server
python main.py

# 3. Server starts at http://localhost:5000
# 4. Test: GET http://localhost:5000/ → "Server running!"
```

### Database
- Connection: Windows Trusted Authentication to `localhost\deliveryDB`
- Tables auto-created on startup via `Base.metadata.create_all()`
- No seed data included — populate via API endpoints

---

## ✅ What's Good About This Project

- **Clean layered architecture**: Controller → Service → Repository → Model separation is well-structured
- **DTO pattern**: Separate serialization layer for API responses
- **Smart VRP approach**: State Space Search with pruning is a solid algorithm choice for multi-stop delivery routing
- **Real travel times**: Uses Google Maps Distance Matrix (not just Haversine distances)
- **In-memory cache**: Google Maps results are cached — avoids redundant API calls
- **Nearest-neighbor within groups**: Recipients within a center group are ordered by proximity for realistic geographic sequence
- **Gale-Shapley matching**: Well-known stable matching algorithm adapted for food delivery
- **Two-phase matching**: Phase 1 finds best matches, Phase 2 fills remaining capacity

---

## 🔧 Recommended Fix Priority

1. **Move API key** to environment variable only (remove hardcoded default)
2. **Hash passwords** with bcrypt
3. **Add JWT authentication** middleware
4. **Clean up** — remove commented-out code, duplicate imports, and legacy VRP files (`engine.py`, `state.py`)
5. **Add JSON error handler** in main.py
6. **Add input validation** in controllers
7. **Set up proper logging** (replace `print()` with `logging` module)
8. **Add Alembic** for database migrations
9. **Normalize naming conventions** across models

---

---

## 🖥 Frontend Structure

The frontend is a **React + TypeScript + Vite** application located in `client last/`.

### Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `Home.tsx` | Landing page — red & white Ezer Mitzion brand, hero section, "How It Works", cards, stats |
| `/login` | `Login.tsx` | Login form — authenticates volunteers, recipients, and distribution centers |
| `/RecipientSignUp` | `RecipientSignUp.tsx` | Recipient registration with Google Maps address autocomplete |
| `/DistributionCenterSignUp` | `DistributionCenterSignUp.tsx` | Distribution center registration |
| `/volunteerSignUp` | `VolunteerSignUp.tsx` | Volunteer registration — selects vehicle type (1-5) |
| `/volunteer-home` | `VolunteerHome.tsx` | **Volunteer dashboard** — send delivery request, view optimized route with Google Maps |
| `/recipient-home` | `RecipientHome.tsx` | Recipient welcome page |
| `/dc-home` | `DCHome.tsx` | Distribution center welcome page |

### VolunteerHome — Smart Route System
The volunteer dashboard is the most complex page:
1. **Request form**: Address input (Google Autocomplete) + available time
2. **API call**: `POST /api/volunteer_request/run_route/<id>`
3. **Smart loading**: Shows "computing..." with algorithm description
4. **Route display**: Color-coded timeline (🟢 start → 🔵 pickup → 🔴 deliver)
5. **Google Map**: Full interactive map with markers, polylines, info windows, and legend
6. **Step details**: Each step shows the center name, recipient name, meal count, and action type

### Key Client Files

| File | Purpose |
|------|---------|
| `src/routs.tsx` | React Router configuration |
| `src/config.ts` | API base URL (`/api`) |
| `src/server/*.tsx` | API call modules (axios) |
| `src/model/*.ts` | TypeScript types |
| `src/style/*.css` | Stylesheets — red & white brand (#C8102E) |
| `src/components/signUp/*.tsx` | Registration forms |
| `src/components/VolunteerHome.tsx` | Main volunteer dashboard |

### Ezer Mitzion Brand

All pages use the **red & white** brand palette:
- Primary: `#C8102E` (deep crimson)
- Bright: `#E6344A`
- Dark: `#8B0000`
- Background: `#FFF5F5` (cream with red undertone)
- The Ezer Mitzion logo (`public/1.png`) appears on every page

---

## 🔄 Recent Updates (July 2026)

### Frontend
- **VolunteerHome rebuilt**: Full dashboard with route request, Google Maps, and color-coded timeline
- **All pages branded**: Red & white palette applied consistently to Home, Login, all 3 SignUp forms, DCHome, RecipientHome
- **Ezer Mitzion logo** added to every page header
- **"How It Works" section** added to Home page — 3-step visual explanation
- **Smart algorithm messaging**: "State Space Search" badge, loading explanations
- **Vehicle type dropdown**: Now shows all 5 types (אופנוע/Mini/Private/Station/מסחרי) with correct DB values

### Backend
- **`build_groups()` enriched**: Now returns `center_name`, `recipient_names`, `recipient_meals` per group
- **`build_detailed_route()` enriched**: Each step now has `label` (name), `detail` (description), `meals` (count), `action` (pickup/deliver/start)
- **Frontend API**: `VolunteerRequest.tsx` created — calls `POST /volunteer_request/run_route/<id>`

---

*Last updated: July 2026 | Project: SmartPath Server*
