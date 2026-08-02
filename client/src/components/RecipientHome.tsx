import React, { useEffect, useState } from "react";
import "../style/RecipientHome.css";
import { addRecipientRequest } from "../server/RecipientRequest";
import { updateRecipient } from "../server/Recipient";
import { base_url } from "../config";
import { LoadScript, Autocomplete } from "@react-google-maps/api";
import NavBar from "./NavBar";
import SharedFooter from "./SharedFooter";
import axios from "axios";

type RecipientRequestItem = {
  id: number;
  RecipientID: number;
  amount_of_meals: number;
  request_date: string;
};

type ViewMode = "none" | "add_request" | "update_address" | "my_requests";

const libraries: ("places")[] = ["places"];
const GOOGLE_KEY = "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY";

const RecipientHome: React.FC = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [view, setView] = useState<ViewMode>("none");

  const handleViewToggle = (nextView: Exclude<ViewMode, "none">) => {
    setView((current) => (current === nextView ? "none" : nextView));
  };

  return (
    <LoadScript googleMapsApiKey={GOOGLE_KEY} libraries={libraries}>
      <div className="rh-page">
        <NavBar />
        <div className="rh-bg" />

        <div className="rh-header-full">
          <img src="/heart.png" alt="לב" className="rh-header-img" />
          <div className="rh-header-content" />
        </div>

        <div className="rh-card rh-card-wide rh-card--flat">

          <div className="rh-home-cards">
            <button className={`rh-home-card${view === "add_request" ? " active" : ""}`} onClick={() => handleViewToggle("add_request")}>
              <img src="/meal.png" alt="בקשת ארוחות" className="rh-home-card-icon-img" />
              <span className="rh-home-card-title">בקשת ארוחות</span>
              <span className="rh-home-card-sub">פתח בקשת סיוע חדשה</span>
            </button>

            <button className={`rh-home-card${view === "update_address" ? " active" : ""}`} onClick={() => handleViewToggle("update_address")}>
              <img src="/home.svg" alt="עדכון כתובת" className="rh-home-card-icon-img" />
              <span className="rh-home-card-title">עדכון כתובת</span>
              <span className="rh-home-card-sub">עדכן את הכתובת שלך</span>
            </button>

            <button className={`rh-home-card${view === "my_requests" ? " active" : ""}`} onClick={() => handleViewToggle("my_requests")}>
              <img src="/text.svg" alt="הבקשות שלי" className="rh-home-card-icon-img" />
              <span className="rh-home-card-title">הבקשות שלי</span>
              <span className="rh-home-card-sub">מעקב אחרי הבקשות והסטטוס</span>
            </button>
          </div>

          {view !== "none" && (
            <div className="rh-main rh-main--card-view">
              {view === "add_request" && <AddRequestView user={user} />}
              {view === "update_address" && <UpdateAddressView user={user} />}
              {view === "my_requests" && <MyRequestsView user={user} />}
            </div>
          )}
        </div>

        <SharedFooter />
      </div>
    </LoadScript>
  );
};

const AddRequestView: React.FC<{ user: any }> = ({ user }) => {
  const [amount, setAmount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const recipientId = Number(user?.id ?? user?.RecipientID ?? user?.recipient_id);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!Number.isInteger(recipientId) || recipientId <= 0) {
      setErr("משתמש לא תקין. יש להתחבר מחדש.");
      setTimeout(() => setErr(null), 4000);
      return;
    }
    if (!Number.isInteger(amount) || amount < 1) {
      setErr("נא להזין לפחות ארוחה אחת.");
      setTimeout(() => setErr(null), 3000);
      return;
    }

    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      await addRecipientRequest({
        id: 0,
        RecipientID: recipientId,
        amount_of_meals: amount,
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="rh-form" onSubmit={submit}>
      <h3 className="rh-section-title">בקשה לארוחות</h3>
      <label className="rh-field">
        <span>כמה ארוחות צריך?</span>
        <input type="number" min="1" value={amount} onChange={(e) => setAmount(Number(e.target.value))} disabled={loading} />
      </label>
      {msg && <div className="rh-message success">{msg}</div>}
      {err && <div className="rh-message error">{err}</div>}
      <button className="rh-submit" type="submit" disabled={loading}>
        {loading ? "שולח..." : "שלח בקשת סיוע"}
      </button>
    </form>
  );
};

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
    if (!address.trim()) {
      setErr("נא להזין כתובת");
      setTimeout(() => setErr(null), 3000);
      return;
    }

    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      await updateRecipient(user?.id, { address });
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="rh-form" onSubmit={submit}>
      <h3 className="rh-section-title">עדכון כתובת</h3>
      <label className="rh-field">
        <span>כתובת</span>
        <Autocomplete onLoad={onLoad} onPlaceChanged={onPlaceChanged}>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="הקלד כתובת ובחר..."
            disabled={loading}
          />
        </Autocomplete>
      </label>
      {msg && <div className="rh-message success">{msg}</div>}
      {err && <div className="rh-message error">{err}</div>}
      <button className="rh-submit" type="submit" disabled={loading}>
        {loading ? "מעדכן..." : "עדכן כתובת"}
      </button>
    </form>
  );
};

const MyRequestsView: React.FC<{ user: any }> = ({ user }) => {
  const [items, setItems] = useState<RecipientRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch(`${base_url}/recipient_request`);
      if (!res.ok) throw new Error(`שגיאה ${res.status}`);
      const data: RecipientRequestItem[] = await res.json();
      setItems(data.filter((i) => i.RecipientID === user?.id).sort((a, b) => Number(b.id) - Number(a.id)));
    } catch (ex: any) {
      setErr(ex?.message || "טעינת הבקשות נכשלה");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h3 className="rh-section-title">הבקשות שלי</h3>
      {loading && <p className="rh-history-empty">טוען...</p>}
      {err && <div className="rh-message error">{err}</div>}
      {!loading && !err && items.length === 0 && <p className="rh-history-empty">עדיין לא נשלחו בקשות.</p>}
      {!loading && items.length > 0 && (
        <div className="rh-history-list">
          {items.map((i) => (
            <div key={i.id} className="rh-history-item">
              <span>{i.amount_of_meals} ארוחות</span>
              <span>{new Date(i.request_date).toLocaleDateString("he-IL")}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecipientHome;
