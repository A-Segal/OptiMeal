


import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../style/form.css";
import { addRecipient } from "../../server/Recipient";
import type { Recipient } from "../../model/Recipient";
import axios from "axios";
import { LoadScript, Autocomplete } from "@react-google-maps/api";

const libraries: ("places")[] = ["places"];

const GOOGLE_MAPS_API_KEY = "AIzaSyAKmXqHHc8_vOP30aKSKvV2C3sH2c67fqY";

const RecipientSignUp: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<Recipient>({
    id: 0,
    fname: "",
    lname: "",
    username: "",
    password: "",
    mail: "",
    phone: "",
    location_lat: 0,
    location_lng: 0,
  });

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
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const createdRecipient = await addRecipient(formData);
      setSuccessMessage("✓ הרישום בוצע בהצלחה!");

      // store user & navigate
      localStorage.setItem(
        "user",
        JSON.stringify({
          ...createdRecipient,
          role: "recipient",
        })
      );
      setTimeout(() => navigate("/recipient-home"), 1200);

      setFormData({
        id: 0,
        fname: "",
        lname: "",
        username: "",
        password: "",
        mail: "",
        phone: "",
        location_lat: 0,
        location_lng: 0,
      });
    } catch (error: any) {
      if (axios.isAxiosError(error)) {
        setErrorMessage(
          error.response?.data?.message ||
            `✗ שגיאת שרת: ${error.response?.status}`
        );
      } else {
        setErrorMessage("✗ שגיאה בשליחת הטופס");
      }
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
            <h2>מוטב</h2>
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
                <h3 className="recipient-signup-section-title">פרטים אישיים</h3>
                <div className="recipient-signup-grid">
                  <div className="recipient-signup-field">
                    <label htmlFor="fname">שם פרטי</label>
                    <input id="fname" type="text" name="fname" value={formData.fname} onChange={handleChange} disabled={isLoading} required />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="lname">שם משפחה</label>
                    <input id="lname" type="text" name="lname" value={formData.lname} onChange={handleChange} disabled={isLoading} required />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="username">שם משתמש</label>
                    <input id="username" type="text" name="username" value={formData.username} onChange={handleChange} disabled={isLoading} required />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="password">סיסמה</label>
                    <input id="password" type="password" name="password" value={formData.password} onChange={handleChange} disabled={isLoading} required />
                  </div>
                </div>
              </section>

              <section className="recipient-signup-section">
                <h3 className="recipient-signup-section-title">פרטי קשר</h3>
                <div className="recipient-signup-grid">
                  <div className="recipient-signup-field">
                    <label htmlFor="mail">אימייל</label>
                    <input id="mail" type="email" name="mail" value={formData.mail} onChange={handleChange} disabled={isLoading} />
                  </div>

                  <div className="recipient-signup-field">
                    <label htmlFor="phone">טלפון</label>
                    <input id="phone" type="tel" name="phone" value={formData.phone} onChange={handleChange} disabled={isLoading} />
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
                  {isLoading ? "...שליחה" : "שלח טופס"}
                </button>
              </div>
            </div>
          </form>
        </div>
      </section>
    </LoadScript>
  );
};

export default RecipientSignUp;