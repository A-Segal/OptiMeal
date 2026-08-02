import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../style/form.css";
import { addVolunteer } from "../../server/Volunteer";
import type { Volunteer } from "../../model/Volunteer";
import axios from "axios";

const VEHICLE_TYPES = [
  { value: 1, label: "אופנוע", capacity: 1 },
  { value: 2, label: "Mini", capacity: 3 },
  { value: 3, label: "Private", capacity: 6 },
  { value: 4, label: "Station", capacity: 10 },
  { value: 5, label: "מסחרי", capacity: 20 },
];

const VolunteerSignUp: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<Volunteer>({
    id: 0,
    fname: "",
    lname: "",
    username: "",
    password: "",
    mail: "",
    phone: "",
  });

  const [capacity, setCapacity] = useState<number>(1);
  const [open, setOpen] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
      const payload = {
        ...formData,
        vehicle_capacity: capacity, // שולח את הערך ישירות 1-5
      };

      const createdVolunteer = await addVolunteer(payload);

      console.log("RESULT:", createdVolunteer);

      setSuccessMessage("ההרשמה בוצעה בהצלחה");

      // store user & navigate
      localStorage.setItem("user", JSON.stringify({ ...payload, role: "volunteer" }));
      setTimeout(() => navigate("/volunteer-home"), 1200);

      setFormData({
        id: 0,
        fname: "",
        lname: "",
        username: "",
        password: "",
        mail: "",
        phone: "",
      });

      setCapacity(1);
      setOpen(false);
    } catch (error: any) {
      if (axios.isAxiosError(error)) {
        setErrorMessage(
          error.response?.data?.message ||
            `שגיאת שרת: ${error.response?.status}`
        );
      } else {
        setErrorMessage("שגיאה בשליחת הטופס");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="recipient-signup-wrap">
      <div className="recipient-signup-card">
        <header className="recipient-signup-header recipient-signup-card-header">
          <button type="button" className="recipient-signup-exit" onClick={() => navigate("/")} aria-label="יציאה">
            ×
          </button>
          <img src="/optimeal.png" alt="עזר מציון" className="page-logo" />
          <h2>מתנדב</h2>
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
                  <input id="fname" name="fname" value={formData.fname} onChange={handleChange} required />
                </div>

                <div className="recipient-signup-field">
                  <label htmlFor="lname">שם משפחה</label>
                  <input id="lname" name="lname" value={formData.lname} onChange={handleChange} required />
                </div>

                <div className="recipient-signup-field">
                  <label htmlFor="username">שם משתמש</label>
                  <input id="username" name="username" value={formData.username} onChange={handleChange} required />
                </div>

                <div className="recipient-signup-field">
                  <label htmlFor="password">סיסמה</label>
                  <input id="password" type="password" name="password" value={formData.password} onChange={handleChange} required />
                </div>
              </div>
            </section>

            <section className="recipient-signup-section">
              <h3 className="recipient-signup-section-title">פרטי קשר ורכב</h3>
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
                  <label>גודל רכב</label>
                  <div className="custom-dropdown">
                    <button type="button" className="dropdown-btn" onClick={() => setOpen((p) => !p)} disabled={isLoading}>
                      {VEHICLE_TYPES.find((v) => v.value === capacity)?.label || "בחר"}
                    </button>

                    {open && (
                      <div className="dropdown-menu">
                        {VEHICLE_TYPES.map((vehicle) => (
                          <div key={vehicle.value} onClick={() => { setCapacity(vehicle.value); setOpen(false); }}>
                            {vehicle.label}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>

            <div className="recipient-signup-submit">
              <button type="submit" disabled={isLoading}>
                {isLoading ? "שולח..." : "הרשמה"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </section>
  );
};

export default VolunteerSignUp;