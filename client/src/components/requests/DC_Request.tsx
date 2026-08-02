import React, { useState } from "react";
import axios from "axios";
import "../../style/form.css";
import type { DC_Request } from "../../model/DC_Request";
import { addRequest } from "../../server/DC_Request";

const emptyForm = {
  amount_of_meals: 0,
  type: 0,
};

const DCRequest: React.FC = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [formData, setFormData] = useState({
    amount_of_meals: 0,
    type: 0,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: Number(value),
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const payload: DC_Request = {
        id: 0,
        DistributionCenterID: user?.id, // מהמשתמש המחובר
        amount_of_meals: formData.amount_of_meals,
        type: formData.type,
        request_date: new Date(), // אוטומטי היום
      };

      await addRequest(payload);

      setFormData(emptyForm);
      setSuccessMessage("✔ הבקשה נשלחה בהצלחה");

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      if (axios.isAxiosError(error)) {
        setErrorMessage(
          error.response?.data?.message ||
            `✖ שגיאת שרת: ${error.response?.status}`
        );
      } else {
        setErrorMessage("✖ שגיאה כללית בשליחת הבקשה");
      }

      setTimeout(() => setErrorMessage(null), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="recipient-signup-wrap">
      <div className="recipient-signup-card">

        <header className="recipient-signup-header">
          <span className="eyebrow">DC Request</span>
          <h2>יצירת בקשה חדשה</h2>
          <p>הזן כמות ארוחות וסוג בקשה</p>
        </header>

        <form className="recipient-signup-form" onSubmit={handleSubmit}>

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

          <div className="recipient-signup-field">
            <label>כמות ארוחות</label>
            <input
              type="number"
              name="amount_of_meals"
              value={formData.amount_of_meals}
              onChange={handleChange}
            />
          </div>

          <div className="recipient-signup-field">
            <label>סוג בקשה</label>
            <select name="type" value={formData.type} onChange={handleChange}>
              <option value={0}>רגיל</option>
              <option value={1}>דחוף</option>
              <option value={2}>חירום</option>
            </select>
          </div>

          <div className="recipient-signup-field">
            <label>תאריך</label>
            <input
              type="text"
              value={new Date().toLocaleDateString()}
              disabled
            />
          </div>

          <div className="recipient-signup-submit">
            <button type="submit" disabled={isLoading}>
              {isLoading ? "שולח..." : "שלח בקשה"}
            </button>
          </div>

        </form>
      </div>
    </section>
  );
};

export default DCRequest;