import React, { useState, useEffect, useRef, useMemo } from "react";
import { LoadScript, Autocomplete, GoogleMap, Marker, Polyline, InfoWindow, DirectionsRenderer } from "@react-google-maps/api";
import { runVolunteerRoute, type RunRouteRequest } from "../server/VolunteerRequest";
import { getVehicleByVolunteer, upsertVehicle } from "../server/Vehicle";
import axios from "axios";
import NavBar from "./NavBar";
import SharedFooter from "./SharedFooter";
import "../style/VolunteerHome.css";

const libraries: ("places")[] = ["places"];
const GOOGLE_MAPS_API_KEY = "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY";

/* ── vehicle options ── */
const VEHICLE_OPTIONS = [
  { capacity: 1, label: "אופנוע",  icon: "🏍️", meals: 20,  desc: "עד 20 מנות" },
  { capacity: 2, label: "מיני",    icon: "🚗", meals: 60,  desc: "עד 60 מנות" },
  { capacity: 3, label: "פרטי",    icon: "🚙", image: "/private.png", meals: 120, desc: "עד 120 מנות" },
  { capacity: 4, label: "סטיישן",  icon: "🚐", meals: 250, desc: "עד 250 מנות" },
  { capacity: 5, label: "מסחרי",   icon: "🚛", image: "/mischari.png", meals: 500, desc: "עד 500 מנות" },
];

/* ── types ── */
type ActionType = "start" | "pickup" | "deliver";

interface RouteStep {
  step: number; type: string; action: ActionType;
  center_id: number | null; assignment_id: number | null;
  lat: number; lng: number; label: string; detail: string;
  address?: string; meals: number;
}

interface RouteResult {
  volunteer_id: number; start_location: { lat: number; lng: number };
  route: number[]; detailed_route: RouteStep[];
  groups_count: number; vehicle_capacity: number;
  total_meals: number; final_time_minutes: number;
  visited_count: number; message?: string;
}

/* ── action meta ── */
const actionMeta: Record<ActionType, { icon: string; color: string; colorHex: string; image?: string }> = {
  start: { icon: "🚗", color: "step--start", colorHex: "#22C55E", image: "/car3.svg" },
  pickup: { icon: "🏢", color: "step--pickup", colorHex: "#3B82F6", image: "/center.svg" },
  deliver: { icon: "🏠", color: "step--deliver", colorHex: "#EF4444", image: "/home.svg" },
};

const ROUTE_MAP_STYLES: google.maps.MapTypeStyle[] = [
  { featureType: "all", elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { featureType: "poi", stylers: [{ visibility: "off" }] },
  { featureType: "transit", stylers: [{ visibility: "off" }] },
  { featureType: "administrative", elementType: "labels.text.fill", stylers: [{ color: "#7f8c8d" }] },
  { featureType: "landscape", elementType: "geometry", stylers: [{ color: "#f3f5f7" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#dbeafe" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#e4e8ee" }] },
  { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#8b95a1" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#d9dee6" }] },
];

const ROUTE_HERO_TEXT = "המסלול הותאם עבורך באופן חכם, תוך התחשבות במרחקי הנסיעה, קיבולת הרכב והזמן הפנוי שלך, כדי להבטיח חלוקה יעילה ככל האפשר.";

function keepLastWordsTogether(text: string): string {
  const lastSpaceIndex = text.lastIndexOf(" ");
  if (lastSpaceIndex === -1) {
    return text;
  }
  return `${text.slice(0, lastSpaceIndex)}\u00A0${text.slice(lastSpaceIndex + 1)}`;
}

function formatTime(minutes: number): string {
  if (!Number.isFinite(minutes) || minutes <= 0) {
    return "0 דק׳";
  }

  if (minutes < 1) {
    return `${minutes.toFixed(2)} דק׳`;
  }

  const totalMinutes = Math.round(minutes * 10) / 10;
  const h = Math.floor(totalMinutes / 60);
  const m = Math.round((totalMinutes % 60) * 10) / 10;

  if (h === 0) {
    return Number.isInteger(m) ? `${m} דק׳` : `${m.toFixed(1)} דק׳`;
  }

  if (m === 0) {
    return `${h} ש׳`;
  }

  return Number.isInteger(m) ? `${h} ש׳ ${m} דק׳` : `${h} ש׳ ${m.toFixed(1)} דק׳`;
}

/* ================================================================== */
/* ── MAP COMPONENT ── */
const RouteMap: React.FC<{ steps: RouteStep[]; height?: string }> = ({ steps, height = "400px" }) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [directionsLoading, setDirectionsLoading] = useState(false);
  const [mapRef, setMapRef] = useState<google.maps.Map | null>(null);
  const path = useMemo(() => steps.map((s) => ({ lat: s.lat, lng: s.lng })), [steps]);
  const center = useMemo(() => steps.length === 0 ? { lat: 31.77, lng: 35.21 } : { lat: steps[0].lat, lng: steps[0].lng }, [steps]);

  useEffect(() => {
    let cancelled = false;

    if (steps.length < 2 || !window.google?.maps) {
      setDirections(null);
      setDirectionsLoading(false);
      return;
    }

    setDirectionsLoading(true);
    const service = new google.maps.DirectionsService();
    const origin = { lat: steps[0].lat, lng: steps[0].lng };
    const destination = { lat: steps[steps.length - 1].lat, lng: steps[steps.length - 1].lng };
    const waypoints = steps.slice(1, -1).map((s) => ({
      location: { lat: s.lat, lng: s.lng },
      stopover: true,
    }));

    service.route(
      {
        origin,
        destination,
        waypoints,
        optimizeWaypoints: false,
        travelMode: google.maps.TravelMode.DRIVING,
      },
      (result, status) => {
        if (cancelled) {
          return;
        }

        if (status === google.maps.DirectionsStatus.OK && result) {
          setDirections(result);
        } else {
          // Fallback to straight polyline when Directions API cannot return a route.
          setDirections(null);
        }

        setDirectionsLoading(false);
      }
    );

    return () => {
      cancelled = true;
    };
  }, [steps]);

  useEffect(() => {
    if (!mapRef || steps.length === 0 || !window.google?.maps) {
      return;
    }

    if (directions?.routes?.[0]?.bounds) {
      mapRef.fitBounds(directions.routes[0].bounds);
      return;
    }

    const bounds = new google.maps.LatLngBounds();
    steps.forEach((s) => bounds.extend({ lat: s.lat, lng: s.lng }));
    mapRef.fitBounds(bounds);
  }, [mapRef, directions, steps]);

  const getMarkerIcon = (step: RouteStep): google.maps.Icon | google.maps.Symbol => {
    if (step.action === "pickup") {
      return {
        url: "/center.svg",
        scaledSize: new google.maps.Size(38, 38),
        anchor: new google.maps.Point(19, 19),
      };
    }

    if (step.action === "deliver") {
      return {
        url: "/home.svg",
        scaledSize: new google.maps.Size(38, 38),
        anchor: new google.maps.Point(19, 19),
      };
    }

    return {
      url: "/car3.svg",
      scaledSize: new google.maps.Size(40, 40),
      anchor: new google.maps.Point(20, 20),
    };
  };

  return (
    <div className="vh-map-wrap">
      <GoogleMap
        onLoad={(map) => setMapRef(map)}
        mapContainerStyle={{ width: "100%", height, touchAction: "auto" }}
        center={center}
        zoom={12}
        options={{
          disableDefaultUI: false,
          zoomControl: true,
          streetViewControl: false,
          mapTypeControl: false,
          mapTypeId: "roadmap",
          styles: ROUTE_MAP_STYLES,
          clickableIcons: false,
          gestureHandling: "none",
          scrollwheel: false,
          draggable: false,
          fullscreenControl: true,
        }}>
        {directions ? (
          <DirectionsRenderer
            directions={directions}
            options={{
              suppressMarkers: true,
              polylineOptions: {
                strokeColor: "#0F3D91",
                strokeOpacity: 0.96,
                strokeWeight: 7,
                icons: [
                  {
                    icon: {
                      path: "M 0,-1 0,1",
                      strokeOpacity: 0.75,
                      scale: 4,
                      strokeColor: "#FFFFFF",
                    },
                    offset: "0",
                    repeat: "1px",
                  },
                ],
              },
            }}
          />
        ) : !directionsLoading ? (
          <Polyline
            path={path}
            options={{
              strokeColor: "#0F3D91",
              strokeOpacity: 0.9,
              strokeWeight: 6,
              icons: [{ icon: { path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW }, offset: "100%", repeat: "150px" }],
            }}
          />
        ) : null}
        {directionsLoading && (
          <div className="vh-map-loading">טוען מפה...</div>
        )}
        {steps.map((step, i) => (
          <Marker key={i} position={{ lat: step.lat, lng: step.lng }}
            icon={getMarkerIcon(step)}
            onMouseOver={() => setHoveredIdx(i)} onMouseOut={() => setHoveredIdx(null)}>
            {hoveredIdx === i && (
              <InfoWindow>
                <div style={{ fontFamily: "Rubik, Assistant, sans-serif", textAlign: "right", minWidth: 120 }}>
                  <strong>{step.label}</strong>
                  {step.detail && <div style={{ fontSize: 12, color: "#666" }}>{step.detail}</div>}
                  {step.address && <div style={{ fontSize: 11, color: "#999" }}>{step.address}</div>}
                </div>
              </InfoWindow>
            )}
          </Marker>
        ))}
      </GoogleMap>
      <div className="vh-map-legend">
        <div className="vh-map-legend-item"><img src="/car3.svg" alt="start" className="vh-map-legend-icon" /><span>התחלה</span></div>
        <div className="vh-map-legend-item"><img src="/center.svg" alt="center" className="vh-map-legend-icon" /><span>איסוף</span></div>
        <div className="vh-map-legend-item"><img src="/home.svg" alt="home" className="vh-map-legend-icon" /><span>חלוקה</span></div>
      </div>
    </div>
  );
};

/* ================================================================== */
/* ── MAIN COMPONENT ── */
const VolunteerHome: React.FC = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const volunteerId = Number(user?.id ?? user?.VolunteerID ?? 0);
  const startAddressStorageKey = useMemo(
    () => `volunteer_start_address_${volunteerId || "guest"}`,
    [volunteerId]
  );
  const lastRouteStorageKey = useMemo(
    () => `volunteer_last_route_${volunteerId || "guest"}`,
    [volunteerId]
  );

  /* ── vehicle state ── */
  const [selectedCapacity, setSelectedCapacity] = useState<number | null>(null);
  const [vehicleLoading, setVehicleLoading] = useState(true);
  const [vehicleMsg, setVehicleMsg] = useState<string | null>(null);

  /* ── route state ── */
  const [showForm, setShowForm] = useState(false);
  const [address, setAddress] = useState("");
  const [availableTime, setAvailableTime] = useState<number>(3);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routeResult, setRouteResult] = useState<RouteResult | null>(null);
  const [showMap, setShowMap] = useState(false);
  const [animatedRouteText, setAnimatedRouteText] = useState("");
  const [hasLastRoute, setHasLastRoute] = useState(false);

  /* ── load vehicle ── */
  useEffect(() => {
    if (!volunteerId) return;
    getVehicleByVolunteer(volunteerId).then((v) => {
      if (v) {
        setSelectedCapacity(v.capacity);
      }
    }).finally(() => setVehicleLoading(false));
  }, [volunteerId]);

  useEffect(() => {
    const savedAddress = localStorage.getItem(startAddressStorageKey);
    const fallbackAddress = user?.address || user?.start_address || "";
    setAddress(savedAddress || fallbackAddress);
  }, [startAddressStorageKey, user?.address, user?.start_address]);

  useEffect(() => {
    const raw = localStorage.getItem(lastRouteStorageKey);
    if (!raw) {
      setHasLastRoute(false);
      return;
    }

    try {
      const parsed = JSON.parse(raw) as RouteResult;
      const isValid = Boolean(parsed?.detailed_route?.length);
      setHasLastRoute(isValid);
      if (!isValid) {
        localStorage.removeItem(lastRouteStorageKey);
      }
    } catch {
      setHasLastRoute(false);
      localStorage.removeItem(lastRouteStorageKey);
    }
  }, [lastRouteStorageKey]);

  useEffect(() => {
    if (!routeResult || routeResult.detailed_route.length === 0) {
      setAnimatedRouteText("");
      return;
    }

    setAnimatedRouteText("");
    let charIndex = 0;
    const timer = window.setInterval(() => {
      charIndex += 1;
      setAnimatedRouteText(ROUTE_HERO_TEXT.slice(0, charIndex));
      if (charIndex >= ROUTE_HERO_TEXT.length) {
        window.clearInterval(timer);
      }
    }, 34);

    return () => window.clearInterval(timer);
  }, [routeResult]);

  /* ── handle vehicle select ── */
  const handleVehicleSelect = async (capacity: number) => {
    setVehicleLoading(true); setVehicleMsg(null);
    try {
      await upsertVehicle(volunteerId, capacity);
      setSelectedCapacity(capacity);
      setVehicleMsg("✅ סוג הרכב עודכן בהצלחה");
      setTimeout(() => setVehicleMsg(null), 3000);
    } catch {
      setVehicleMsg("❌ שגיאה בעדכון הרכב");
    } finally { setVehicleLoading(false); }
  };

  /* ── route submit ── */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) { setError("יש להזין כתובת"); return; }
    const startAddress = address.trim();
    setLoading(true); setError(null); setShowMap(false);
    try {
      localStorage.setItem(startAddressStorageKey, startAddress);
      const data: RunRouteRequest = { address: startAddress, available_time: availableTime };
      const result: RouteResult = await runVolunteerRoute(volunteerId, data);
      setRouteResult(result);
      if (result?.detailed_route?.length) {
        localStorage.setItem(lastRouteStorageKey, JSON.stringify(result));
        setHasLastRoute(true);
      }
      setShowMap(false);

      const firstStepAddress = result?.detailed_route?.[0]?.address;
      if (firstStepAddress) {
        setAddress(firstStepAddress);
        localStorage.setItem(startAddressStorageKey, firstStepAddress);
      }

      setShowForm(false);
    } catch (err: any) {
      setError(axios.isAxiosError(err) ? err.response?.data?.error || `שגיאת שרת: ${err.response?.status}` : "שגיאה בשליחת הבקשה");
    } finally { setLoading(false); }
  };

  const showLastRequest = () => {
    const raw = localStorage.getItem(lastRouteStorageKey);
    if (!raw) {
      setError("לא נמצאה בקשה אחרונה.");
      return;
    }

    try {
      const parsed = JSON.parse(raw) as RouteResult;
      if (!parsed?.detailed_route?.length) {
        setError("לא נמצאה בקשה אחרונה תקינה.");
        return;
      }

      setRouteResult(parsed);
      setShowForm(false);
      setShowMap(false);
      setError(null);

      const firstStepAddress = parsed.detailed_route[0]?.address;
      if (firstStepAddress) {
        setAddress(firstStepAddress);
      }
    } catch {
      setError("לא ניתן לטעון את הבקשה האחרונה.");
    }
  };

  const reset = () => {
    setRouteResult(null); setAvailableTime(3); setError(null); setShowMap(false);
  };

  const hasRoute = routeResult && routeResult.detailed_route.length > 0;
  const isFullRouteView = Boolean(routeResult && hasRoute);
  const routeStartAddress = routeResult?.detailed_route?.[0]?.address || address;

  useEffect(() => {
    if (!routeResult || hasRoute) {
      return;
    }

    const timer = window.setTimeout(() => {
      reset();
    }, 2200);

    return () => window.clearTimeout(timer);
  }, [routeResult, hasRoute]);

  return (
    <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY} libraries={libraries}>
      <div className={`vh-page${isFullRouteView ? " vh-page--route" : ""}`}>
        <NavBar />
        <div className="vh-bg" />

        {/* ════════════ FULL-WIDTH HEADER ════════════ */}
        <div className="vh-header-full">
          <img src="/carnice.png" alt="רכב משלוחים" className="vh-header-img" />
          <div className="vh-header-content">
            <div className="vh-header-left">
              {/* <img src="/1.png" alt="עזר מציון" className="vh-logo" /> */}
            </div>
            <div className="vh-header-center">
            </div>
          </div>
        </div>

        {/* ════════════ SECTIONS GRID ════════════ */}
        {!isFullRouteView && <div className="vh-dashboard">

          {/* ═══ PANEL: רכב ═══ */}
          <div className={`vh-panel ${showForm ? "vh-panel--dimmed" : ""}`}>
            <div className="vh-panel-header">
              <h2 className="vh-panel-title">עדכון סוג רכב</h2>
            </div>
            <p className="vh-card-hint">לחץ כדי לבחור ולעדכן את סוג הרכב</p>
            {vehicleMsg && <div className={`vh-toast ${vehicleMsg.startsWith("✅") ? "vh-toast--ok" : "vh-toast--err"}`}>{vehicleMsg}</div>}
            {vehicleLoading ? (
              <div className="vh-loading-inline"><div className="vh-spinner-sm" /><span>טוען...</span></div>
            ) : (
              <div className="vh-vehicle-grid">
                {VEHICLE_OPTIONS.map((opt) => (
                  <button
                    key={opt.capacity}
                    className={`vh-vehicle-card ${selectedCapacity === opt.capacity ? "vh-vehicle-card--active" : ""}`}
                    onClick={() => handleVehicleSelect(opt.capacity)}
                    title={opt.desc}
                  >
                    {opt.image ? (
                      <img src={opt.image} alt={opt.label} className="vh-vehicle-icon-img" />
                    ) : (
                      <span className="vh-vehicle-icon">{opt.icon}</span>
                    )}
                    <span className="vh-vehicle-label">{opt.label}</span>
                    <span className="vh-vehicle-families">{opt.meals} מנות</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ═══ PANEL: מסלול ═══ */}
          <div className={`vh-panel ${showForm ? "vh-panel--focused" : ""}`}>
            <div className="vh-panel-header">
              {/* <span className="vh-panel-icon">🗺️</span> */}
              <h2 className="vh-panel-title">בקשת מסלול</h2>
            </div>
            {!showForm && !loading && !routeResult && (
              <p className="vh-card-hint">לחץ כדי לפתוח בקשת מסלול חדשה</p>
            )}
            {!showForm && !loading && !routeResult && (
              <div className="vh-card-empty">
                {/* <div className="vh-card-empty-icon">🚚</div> */}
                <button
                  type="button"
                  className="vh-btn-main"
                  onClick={() => setShowForm(true)}
                >
                  שליחת בקשה למסלול
                </button>
              </div>
            )}
            {showForm && (
              <form className="vh-form" onSubmit={handleSubmit}>
                {error && <div className="vh-msg vh-msg--err">{error}</div>}
                <div className="vh-field">
                  <label>כתובת התחלה</label>
                  <Autocomplete onLoad={(a) => { autocompleteRef.current = a; }} onPlaceChanged={() => {
                    const place = autocompleteRef.current?.getPlace();
                    if (place?.formatted_address) setAddress(place.formatted_address);
                  }}>
                    <input type="text" placeholder="הקלד כתובת..." value={address}
                      onChange={(e) => setAddress(e.target.value)} disabled={loading} required />
                  </Autocomplete>
                </div>
                <div className="vh-field">
                  <label>זמן פנוי (שעות)</label>
                  <div className="vh-time-control">
                    <input
                      type="range"
                      min={0.1}
                      max={24}
                      step={0.1}
                      value={availableTime}
                      onChange={(e) => setAvailableTime(Number(e.target.value))}
                      disabled={loading}
                    />
                    <span className="vh-time-value">{availableTime.toFixed(1)} שעות</span>
                  </div>
                </div>
                <div className="vh-form-actions">
                  <button type="submit" className="vh-btn-submit" disabled={loading}>
                    {loading ? "מחשב מסלול..." : "שלח בקשה"}
                  </button>
                  <button type="button" className="vh-btn-cancel"
                    onClick={() => { setShowForm(false); setError(null); }} disabled={loading}>ביטול</button>
                </div>
              </form>
            )}
            {loading && (
              <div className="vh-loading">
                <img src="/optimeal.png" alt="OptiMeal loading" className="vh-loading-coin" />
                <p className="vh-loading-title">המערכת מתאימה עבורך מסלול חלוקה אופטימלי לפי מיקום, קיבולת וזמן פנוי.</p>
                <div className="vh-loading-how" aria-label="איך המערכת עובדת">
                  <h4>איך המערכת עובדת</h4>
                  <div className="vh-loading-how-grid">
                    <div className="vh-loading-how-item"><strong>1</strong><span>מנתחת את נקודת ההתחלה והזמן הפנוי</span></div>
                    <div className="vh-loading-how-item"><strong>2</strong><span>מחשבת התאמה למרכזים ולבקשות זמינות</span></div>
                    <div className="vh-loading-how-item"><strong>3</strong><span>בונה מסלול חלוקה ברור ומסודר לביצוע</span></div>
                  </div>
                </div>
              </div>
            )}
            {!showForm && error && !loading && !routeResult && (
              <div className="vh-card-empty">
                <div className="vh-msg vh-msg--err">{error}</div>
                <a
                  href="#"
                  className="vh-action-link vh-action-link--retry"
                  onClick={(e) => {
                    e.preventDefault();
                    setShowForm(true);
                  }}
                >
                  נסה שוב
                </a>
              </div>
            )}
          </div>

          {/* ═══ PANEL: בקשה אחרונה ═══ */}
          <div className="vh-panel">
            <div className="vh-panel-header">
              <h2 className="vh-panel-title">בקשה אחרונה</h2>
            </div>
            <div className="vh-card-empty">
              <p className="vh-card-hint">לחץ כדי לצפות במסלול האחרון שביצעת</p>
              <button
                type="button"
                className="vh-btn-main"
                onClick={showLastRequest}
                disabled={!hasLastRoute}
              >
                הצג בקשה אחרונה
              </button>
              {!hasLastRoute && <small className="vh-route-note">אין מסלול שמור עדיין</small>}
            </div>
          </div>

        </div>}

        {/* ════════════ ROUTE RESULT ════════════ */}
        {routeResult && (
          <>
            {!hasRoute ? (
              <div className="vh-route-card vh-route-card--no-route">
              <div className="vh-route-empty">
                <h2 className="vh-route-title">אין מסלול זמין</h2>
                <p className="vh-route-msg">
                  {routeResult.message || "לא נמצא מסלול מתאים כרגע."}
                </p>
                {hasLastRoute && (
                  <button
                    type="button"
                    className="vh-btn-main"
                    onClick={showLastRequest}
                  >
                    הצג בקשה אחרונה
                  </button>
                )}
              </div>
              </div>
            ) : (
              <section className="vh-route-fullscreen">
                <div className="vh-route-hero">
                  <div className="vh-route-hero-head">
                    <p className="vh-route-subtitle vh-route-subtitle--animated">
                      {keepLastWordsTogether(animatedRouteText)}
                      <span className="vh-route-caret" aria-hidden="true" />
                    </p>
                  </div>
                  <div className="vh-summary-stats">
                    <div className="vh-stat"><span className="vh-stat-num">{routeResult.total_meals}</span><span>מנות</span></div>
                    <div className="vh-stat-divider" />
                    <div className="vh-stat"><span className="vh-stat-num">{routeResult.visited_count}</span><span>מרכזים</span></div>
                    <div className="vh-stat-divider" />
                    <div className="vh-stat"><span className="vh-stat-num">{formatTime(routeResult.final_time_minutes)}</span><span>זמן משוער</span></div>
                  </div>
                  {routeStartAddress && <p className="vh-route-start">נקודת התחלה: {routeStartAddress}</p>}
                  {routeResult.message && <p className="vh-route-note">{routeResult.message}</p>}
                </div>

                <div className="vh-route-content">
                  <div className="vh-route-pane-head">
                    <h3>{showMap ? "מפת מסלול" : "שלבי המסלול"}</h3>
                    <button
                      type="button"
                      className="vh-btn-map"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setShowMap((prev) => !prev);
                      }}
                    >
                      {showMap ? "הצג שלבים" : "🗺️ הצג מפה"}
                    </button>
                  </div>

                  {showMap ? (
                    <div className="vh-route-map-only">
                      <RouteMap steps={routeResult.detailed_route} height="82vh" />
                    </div>
                  ) : (
                    <div className="vh-route-steps-pane vh-route-steps-pane--full">
                      <div className="vh-timeline vh-timeline-scroll">
                        {routeResult.detailed_route.map((step, i) => {
                          const meta = actionMeta[step.action] || actionMeta.start;
                          return (
                            <div key={i} className={`vh-step ${meta.color}`}>
                              <div className="vh-step-marker">
                                {meta.image ? (
                                  <img src={meta.image} alt={step.action} className="vh-step-icon-img" />
                                ) : (
                                  <span className="vh-step-icon">{meta.icon}</span>
                                )}
                              </div>
                              <div className="vh-step-body">
                                <div className="vh-step-header">
                                  <span className="vh-step-label">{step.label}</span>
                                  {step.meals > 0 && (
                                    <span className={`vh-step-badge ${step.action === "pickup" ? "badge--pickup" : "badge--deliver"}`}>
                                      {step.action === "pickup" ? "איסוף" : "חלוקה"} • {step.meals} מנות
                                    </span>
                                  )}
                                </div>
                                {step.detail && <span className="vh-step-sub">{step.detail}</span>}
                                {step.address && <span className="vh-step-addr">{step.address}</span>}
                              </div>
                              {i < routeResult.detailed_route.length - 1 && (
                                <div className={`vh-step-line line--${step.action}`} />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <div className="vh-route-actions">
                  <a
                    href="#"
                    className="vh-action-link vh-action-link--new"
                    onClick={(e) => {
                      e.preventDefault();
                      reset();
                    }}
                  >
                    בקשה חדשה
                  </a>
                </div>
              </section>
            )}
          </>
        )}

        <div className="vh-footer-space">
          <SharedFooter />
        </div>
      </div>
    </LoadScript>
  );
};

export default VolunteerHome;
