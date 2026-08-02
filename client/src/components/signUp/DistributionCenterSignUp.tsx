





import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../style/form.css";
import { addDistributionCenterSignUp } from "../../server/DistributionCenterSignUp";
import type { DistributionCenter } from "../../model/DistributionCenter";
import axios from "axios";

import { LoadScript, Autocomplete } from "@react-google-maps/api";

const libraries: ("places")[] = ["places"];

const GOOGLE_MAPS_API_KEY = "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY";

const emptyForm = {
  fname: "",
  lname: "",
  username: "",
  password: "",
  mail: "",
  phone: "",
  location_lat: 0,
  location_lng: 0,
};

const DistributionCenterSignUp: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] =
    useState<Omit<DistributionCenter, "id">>(emptyForm);

  const [autocomplete, setAutocomplete] =
    useState<google.maps.places.Autocomplete | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const onLoad = (auto: google.maps.places.Autocomplete) => {
    setAutocomplete(auto);
  };

  const onPlaceChanged = () => {
    if (!autocomplete) return;

    const place = autocomplete.getPlace();

    const lat = place.geometry?.location?.lat();
    const lng = place.geometry?.location?.lng();

    if (lat && lng) {
      setFormData((prev) => ({
        ...prev,
        location_lat: lat,
        location_lng: lng,
      }));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();

  // ===== VALIDATION (NEW) =====
  if (
    !formData.fname ||
    !formData.lname ||
    !formData.username ||
    !formData.password ||
    !formData.mail ||
    !formData.phone ||
    !formData.location_lat ||
    !formData.location_lng
  ) {
    setErrorMessage("✖ יש למלא את כל השדות לפני שליחה");
    setTimeout(() => setErrorMessage(null), 3000);
    return;
  }

  setIsLoading(true);
  setErrorMessage(null);
  setSuccessMessage(null);

  try {
    const createdCenter = await addDistributionCenterSignUp({
      id: 0,
      ...formData,
    });

    setFormData(emptyForm);

    setSuccessMessage("✔ נשלח בהצלחה");

    // store user & navigate with backend id
    localStorage.setItem("user", JSON.stringify({ ...createdCenter, role: "distribution_center" }));
    setTimeout(() => navigate("/dc-home"), 1200);

    setTimeout(() => {
      setSuccessMessage(null);
    }, 3000);
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      setErrorMessage(
        error.response?.data?.message ||
          `✖ שגיאת שרת: ${error.response?.status}`
      );
    } else {
      setErrorMessage("✖ שגיאה כללית בשליחת הטופס");
    }

    setTimeout(() => setErrorMessage(null), 3000);
  } finally {
    setIsLoading(false);
  }
};

  return (
    <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY} libraries={libraries}>
      <section className="recipient-signup-wrap">
        <div className="recipient-signup-card">

          <header className="recipient-signup-header recipient-signup-card-header">
            <button type="button" className="recipient-signup-exit" onClick={() => navigate("/")} aria-label="יציאה">
              ×
            </button>
            <img src="/optimeal.png" alt="עזר מציון" className="page-logo" />
            <h2>מרכז</h2>
          </header>

          <form className="recipient-signup-form" onSubmit={handleSubmit}>
            <div className="recipient-signup-layout">
              {errorMessage && (
                <div className="recipient-signup-message error">
                  {errorMessage}
                </div>
              )}

              {successMessage && (
                <div className="recipient-signup-message success">
                  {successMessage}
                </div>
              )}

              <section className="recipient-signup-section">
                <h3 className="recipient-signup-section-title">פרטי חשבון</h3>
                <div className="recipient-signup-grid">
                  <div className="recipient-signup-field">
                    <label htmlFor="fname">שם פרטי</label>
                    <input id="fname" name="fname" value={formData.fname} onChange={handleChange} />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="lname">שם משפחה</label>
                    <input id="lname" name="lname" value={formData.lname} onChange={handleChange} />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="username">שם משתמש</label>
                    <input id="username" name="username" value={formData.username} onChange={handleChange} />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="password">סיסמה</label>
                    <input id="password" type="password" name="password" value={formData.password} onChange={handleChange} />
                  </div>
                </div>
              </section>

              <section className="recipient-signup-section">
                <h3 className="recipient-signup-section-title">פרטי קשר</h3>
                <div className="recipient-signup-grid">
                  <div className="recipient-signup-field">
                    <label htmlFor="mail">אימייל</label>
                    <input id="mail" type="email" name="mail" value={formData.mail} onChange={handleChange} />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="phone">טלפון</label>
                    <input id="phone" type="tel" name="phone" value={formData.phone} onChange={handleChange} />
                  </div>

                  <div className="recipient-signup-field recipient-signup-field--full">
                    <label htmlFor="address">כתובת</label>
                    <Autocomplete onLoad={onLoad} onPlaceChanged={onPlaceChanged}>
                      <input id="address" type="text" placeholder="הקלד כתובת" disabled={isLoading} />
                    </Autocomplete>
                  </div>
                </div>
              </section>

              <div className="recipient-signup-submit">
                <button type="submit" disabled={isLoading}>
                  {isLoading ? "שולח..." : "שלח טופס"}
                </button>
              </div>
            </div>

          </form>
        </div>
      </section>
    </LoadScript>
  );
};

export default DistributionCenterSignUp;