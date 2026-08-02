# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ⚠️ **CRITICAL — Read me first every session.** This file is the authoritative map of the project. Always read it before doing any work. It saves tokens and prevents mistakes.
>
> ⚠️ **Auto-update rule:** Every time you make changes to this project — add a component, change architecture, fix something, complete a task — **update this file automatically**. Keep the "Current State" section current. The user should not need to ask. This file is the single source of truth for future sessions.

## Project Identity

**Ezer Mitzion (עזר מציון) Meal Delivery System** — Client Side (React + TypeScript + Vite).

A platform for managing meal deliveries: Distribution Centers prepare meals, Volunteers deliver them to Recipients. The system runs a Gale-Shapley matching algorithm to pair centers with recipients, and a VRP algorithm for delivery route optimization.

The Python/Flask backend runs at `http://127.0.0.1:5000`.

## Commands

```bash
npm run dev        # Start dev server (Vite HMR, port 5173 default)
npm run build      # TypeScript check + production build → dist/
npm run lint       # ESLint
npm run preview    # Preview production build locally
```

## Architecture

### Core Type (directory `src/model/`)
The central concept is `DeliveryAssignment` — a match between a Distribution Center, a Recipient, and optionally a Volunteer:
```ts
DeliveryAssignment { DistributionCenterID, RecipientID, VolunteerID?, amount_of_meals?, type }
```

**Entity types:** `Recipient`, `Volunteer`, `DistributionCenter`, `Vehicle`, `StaffMember`.

**Request types:** `DC_Request` (center requests meals to prepare), `RecipientRequest` (recipient requests to receive).

**Lookup type:** `Permission` (for StaffMember roles).

### API layer (directory `src/server/`)
Each server file mirrors a backend endpoint. All use `axios` with `base_url` from `config.ts`:
```ts
const base_url = "/api";  // Vite proxies /api → http://127.0.0.1:5000
```
Files: `Auth.tsx`, `Recipient.tsx`, `Volunteer.tsx`, `DistributionCenterSignUp.tsx`, `Vehicle.tsx`, `DC_Request.tsx`, `DeliveryAssigment.tsx`.

Note the typo in filename `DeliveryAssigment.tsx` (missing 'n' — matches the import throughout).

#### **Template — ALWAYS use this when adding a new API call:**
```ts
import axios from "axios";
import { base_url } from "../config";
import type { TypeName } from "../model/TypeName";

export const actionName = async (data: TypeName) => {
  const res = await axios.post(`${base_url}/<endpoint-path>`, data);
  return res.data;
};
```

**Rules for new server calls:**
- File goes in `src/server/` with a matching name (e.g. `Recipient.tsx` for `/recipients` endpoint)
- Import types from `src/model/` — never use `any`
- Use `base_url` from `config.ts` — never hardcode `/api`
- For GET: `axios.get(...)`; for POST: `axios.post(...); for PUT: `axios.put(...)`; for DELETE: `axios.delete(...)`
- Export named functions (not default export) — components using them import by name `{ actionName }`

### Routing (file `src/routs.tsx`)
Uses React Router v7 `createBrowserRouter`:
| Path | Component | Purpose |
|---|---|---|
| `/` | `App` → `Home` | Landing page |
| `/RecipientSignUp` | `RecipientSignUp` | Recipient registration |
| `/DistributionCenterSignUp` | `DistributionCenterSignUp` | DC registration |
| `/volunteerSignUp` | `VolunteerSignUp` | Volunteer registration |
| `/login` | `Login` | Login form |
| `/volunteer-home` | `VolunteerHome` | Volunteer dashboard |
| `/recipient-home` | `RecipientHome` | Recipient dashboard |
| `/dc-home` | `DCHome` | DC dashboard |

### Auth flow
Login → `POST /api/auth/login` → server returns `{ role: "volunteer" | "recipient" | "distribution_center", ... }` → stored in `localStorage("user")` → navigate to role-home. There is no JWT/token mechanism yet — just the user object.

### Design System

**Brand colors:**
- Primary: `#E35205` (orange-red — matches real Ezer Mitzion brand)
- Primary dark: `#C44500`
- Secondary: `#003A70` (dark blue)
- Background: White/cream (`#FFFBF7`, `#F9FAFB`)
- Cards: White with orange-red accent bar (right side, RTL) + shadow

**CSS files:**
- `src/index.css` — Reset, smooth scroll, RTL direction, Hebrew-friendly font stack, body defaults
- `src/style/Home.css` — Full landing page with nav, hero, cards, stats, footer. CSS variables for brand colors.
- `src/style/form.css` — Shared styles for signup/login forms (still purple-themed — needs conversion to red/orange)
- `src/style/DCHme.css` — DC dashboard (dark theme — needs conversion to red/orange+white)

**Font stack:** `"Rubik", "Assistant", "Segoe UI", Arial, sans-serif`

The `body` is set to `direction: rtl` globally. All UI text should be in Hebrew.

**Shared form pattern:** Signup pages use the `recipient-signup-*` CSS classes from `form.css`. The pattern is:
```
.recipient-signup-wrap > .recipient-signup-card > .recipient-signup-header + .recipient-signup-form
```

### Google Maps Integration
Signup forms for `RecipientSignUp` and `DistributionCenterSignUp` use `@react-google-maps/api` `Autocomplete` to capture address → lat/lng coordinates. API key is hardcoded in both components (not in `.env`).

### Components Not Yet Integrated
`RunMatchingButton` and `DownloadAssignmentsButton` exist in `src/components/` but are not yet placed on any dashboard. They call the backend matching and assignment endpoints. `DC_Request` form is also available but not yet routed into the DC dashboard.

### Key Imports Pattern
Signup components import from `../../style/form.css` (relative, since they're in `src/components/signUp/`).
Main components import from `../style/Home.css` or `../style/DCHme.css`.

## Current State & Next Steps

**Already working:**
- Home page: full design — sticky nav with SVG logo, hero section with animated logo, cards with orange accent, stats bar, footer. Ezer Mitzion brand colors (orange-red + dark blue).
- `src/style/Home.css` restored and aligned with current `Home.tsx` + `NavBar.tsx` class usage (hero/nav/how/stats/footer + dropdown + speaker lane).
- All signup forms, login, basic role-based dashboards.
- `index.html` updated: Hebrew title, lang="he", dir="rtl".

**Needs work:**
1. Convert `form.css` from purple theme to orange-red/blue (Ezer Mitzion colors)
2. Convert `DCHme.css` from dark theme to light Ezer Mitzion style
3. Style `VolunteerHome` and `RecipientHome` (currently plain text with inline styles)
4. Integrate `RunMatchingButton`, `DownloadAssignmentsButton`, and `DC_Request` into dashboards
5. Build the matching algorithm UI and VRP route visualization
6. JWT/token-based auth instead of raw user object in localStorage
7. Protected routes (redirect to login if no user in localStorage)
8. Replace emoji card icons with proper SVG icons
