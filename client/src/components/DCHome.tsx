import React, { useEffect, useState } from "react";
import "../style/DCHme.css";
import { addRequest } from "../server/DC_Request";
import { updateDistributionCenter } from "../server/DistributionCenterSignUp";
import { base_url } from "../config";
import { LoadScript, Autocomplete } from "@react-google-maps/api";
import NavBar from "./NavBar";
import SharedFooter from "./SharedFooter";
import axios from "axios";

/* ───────── types ───────── */
type DCRequestItem = {
  id: number;
  DistributionCenterID: number;
  amount_of_meals: number;
  request_date: string;
};

type ViewMode = "none" | "add_request" | "update_address" | "my_requests";

const libraries: ("places")[] = ["places"];
const GOOGLE_KEY = "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY";

/* ───────── main ───────── */
const DCHome: React.FC = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [view, setView] = useState<ViewMode>("none");

  const handleViewToggle = (nextView: Exclude<ViewMode, "none">) => {
    setView((current) => (current === nextView ? "none" : nextView));
  };

  return (
    <LoadScript googleMapsApiKey={GOOGLE_KEY} libraries={libraries}>
      <div className="dc-page">
        <NavBar />
        <div className="dc-bg" />

        <div className="dc-header-full">
          <img src="/heart.png" alt="לב" className="dc-header-img" />
          <div className="dc-header-content" />
        </div>

        <div className="dc-card dc-card--flat">

          <div className="dc-home-cards">
            <button className={`dc-home-card${view === "add_request" ? " active" : ""}`} onClick={() => handleViewToggle("add_request")}>
              <img src="/meal.png" alt="בקשת ארוחות" className="dc-home-card-icon-img" />
              <span className="dc-home-card-title">הכנת ארוחות</span>
              <span className="dc-home-card-sub">הכן ארוחות חדשות לחלוקה</span>
            </button>

            <button className={`dc-home-card${view === "update_address" ? " active" : ""}`} onClick={() => handleViewToggle("update_address")}>
              <img src="/center.svg" alt="עדכון כתובת" className="dc-home-card-icon-img" />
              <span className="dc-home-card-title">עדכון כתובת</span>
              <span className="dc-home-card-sub">עדכן את מיקום המרכז</span>
            </button>

            <button className={`dc-home-card${view === "my_requests" ? " active" : ""}`} onClick={() => handleViewToggle("my_requests")}>
              <img src="/text.svg" alt="הבקשות שלי" className="dc-home-card-icon-img" />
              <span className="dc-home-card-title">הבקשות שלי</span>
              <span className="dc-home-card-sub">צפה בבקשות קודמות וסטטוסים</span>
            </button>
          </div>

          {view !== "none" && (
            <div className="dc-main dc-main--card-view">
              {view === "add_request" && <AddRequestView user={user} />}
              {view === "update_address" && <UpdateAddressView user={user} />}
              {view === "my_requests" && <MyRequestsView user={user} />}
            </div>
          )}
        </div>
      </div>

      <SharedFooter />
    </LoadScript>
  );
};

/* ───────── 1. add request ───────── */
const AddRequestView: React.FC<{ user: any }> = ({ user }) => {
  const [amount, setAmount] = useState(0);
  const [type, setType] = useState(0);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const centerId = Number(user?.id ?? user?.DistributionCenterID ?? user?.distribution_center_id);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!Number.isInteger(centerId) || centerId <= 0) {
      setErr("משתמש מרכז חלוקה לא תקין. התחבר מחדש.");
      setTimeout(() => setErr(null), 4000);
      return;
    }
    if (!Number.isInteger(amount) || amount < 1) {
      setErr("נא להזין לפחות ארוחה אחת.");
      setTimeout(() => setErr(null), 3000);
      return;
    }
    setLoading(true); setErr(null); setMsg(null);
    try {
      await addRequest({
        id: 0,
        DistributionCenterID: centerId,
        amount_of_meals: amount,
        type,
        request_date: new Date(),
      });
      setMsg("✔ הבקשה נשלחה בהצלחה");
      setAmount(0);
      setTimeout(() => setMsg(null), 3000);
    } catch (ex: any) {
      if (axios.isAxiosError(ex)) {
        setErr(ex.response?.data?.error || `שגיאת שרת: ${ex.response?.status}`);
      } else {
        setErr(ex?.message || "שליחת הבקשה נכשלה");
      }
      setTimeout(() => setErr(null), 4000);
    } finally { setLoading(false); }
  };

  return (
    <form className="dc-form" onSubmit={submit}>
      <h3 className="dc-section-title">בקשת ארוחות למחר</h3>
      <label className="dc-field">
        <span>כמות ארוחות</span>
        <input type="number" min="1" value={amount} onChange={(e) => setAmount(Number(e.target.value))} disabled={loading} />
      </label>
      <label className="dc-field">
        <span>סוג ארוחה</span>
        <select value={type} onChange={(e) => setType(Number(e.target.value))} disabled={loading}>
          <option value={0}>יבש</option>
          <option value={1}>חם</option>
        </select>
      </label>
      {msg && <div className="dc-message success">{msg}</div>}
      {err && <div className="dc-message error">{err}</div>}
      <button className="dc-submit" type="submit" disabled={loading}>
        {loading ? "שולח..." : "שלח בקשה"}
      </button>
    </form>
  );
};

/* ───────── 2. update address ───────── */
const UpdateAddressView: React.FC<{ user: any }> = ({ user }) => {
  const [address, setAddress] = useState(user?.address || "");
  const [autocomplete, setAutocomplete] = useState<google.maps.places.Autocomplete | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const onLoad = (auto: google.maps.places.Autocomplete) => setAutocomplete(auto);

  const onPlaceChanged = () => {
    if (!autocomplete) return;
    const place = autocomplete.getPlace();
    if (place?.formatted_address) setAddress(place.formatted_address);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) { setErr("נא להזין כתובת"); setTimeout(() => setErr(null), 3000); return; }
    setLoading(true); setErr(null); setMsg(null);
    try {
      await updateDistributionCenter(user?.id, { address });
      localStorage.setItem("user", JSON.stringify({ ...user, address }));
      setMsg("✔ הכתובת עודכנה בהצלחה");
      setTimeout(() => setMsg(null), 3000);
    } catch (ex: any) {
      if (axios.isAxiosError(ex)) {
        setErr(ex.response?.data?.error || `שגיאת שרת: ${ex.response?.status}`);
      } else {
        setErr(ex?.message || "עדכון הכתובת נכשל");
      }
      setTimeout(() => setErr(null), 4000);
    } finally { setLoading(false); }
  };

  return (
    <form className="dc-form" onSubmit={submit}>
      <h3 className="dc-section-title">עדכון כתובת</h3>
      <label className="dc-field">
        <span>כתובת</span>
        <Autocomplete onLoad={onLoad} onPlaceChanged={onPlaceChanged}>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="הקלד כתובת ובחר מהרשימה..."
            disabled={loading}
          />
        </Autocomplete>
      </label>
      {msg && <div className="dc-message success">{msg}</div>}
      {err && <div className="dc-message error">{err}</div>}
      <button className="dc-submit" type="submit" disabled={loading}>
        {loading ? "מעדכן..." : "עדכן כתובת"}
      </button>
    </form>
  );
};

/* ───────── 3. my requests ───────── */
const MyRequestsView: React.FC<{ user: any }> = ({ user }) => {
  const [items, setItems] = useState<DCRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const centerId = Number(user?.id ?? user?.DistributionCenterID ?? user?.distribution_center_id);

  const load = async () => {
    setLoading(true); setErr(null);
    try {
      const res = await fetch(`${base_url}/dc_requests`);
      if (!res.ok) throw new Error(`שגיאה ${res.status}`);
      const data: DCRequestItem[] = await res.json();
      setItems(data.filter((i) => i.DistributionCenterID === centerId).sort((a, b) => Number(b.id) - Number(a.id)));
    } catch (ex: any) {
      setErr(ex?.message || "טעינת הבקשות נכשלה");
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h3 className="dc-section-title">הבקשות שלי</h3>
      {loading && <p className="dc-history-empty">טוען...</p>}
      {err && <div className="dc-message error">{err}</div>}
      {!loading && !err && items.length === 0 && <p className="dc-history-empty">עדיין לא נשלחו בקשות.</p>}
      {!loading && items.length > 0 && (
        <div className="dc-history-list">
          {items.map((i) => (
            <div key={i.id} className="dc-history-item">
              <span>{i.amount_of_meals} ארוחות</span>
              <span>{new Date(i.request_date).toLocaleDateString("he-IL")}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DCHome;
