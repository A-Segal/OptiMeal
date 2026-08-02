import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../server/Auth";
import "../style/form.css";
import axios from "axios";

const Login: React.FC = () => {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const user = await loginUser(form);

      localStorage.setItem("user", JSON.stringify(user));

      if (user.role === "volunteer") {
        navigate("/volunteer-home");
      } else if (user.role === "recipient") {
        navigate("/recipient-home");
      } else if (user.role === "distribution_center") {
        navigate("/dc-home");
      } else if (user.role === "staff") {
        navigate("/staff-home");
      } else {
        setError("Unknown role");
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message || "Login failed");
      } else {
        setError("Login error");
      }
    } finally {
      setLoading(false);
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
          <h2>כניסה</h2>
        </header>

        <form className="recipient-signup-form" onSubmit={handleLogin}>
          <div className="recipient-signup-layout">
            <section className="recipient-signup-section">
              <h3 className="recipient-signup-section-title">פרטי גישה</h3>
              <div className="recipient-signup-grid">
                <div className="recipient-signup-field recipient-signup-field--full">
                  <label htmlFor="username">שם משתמש</label>
                  <input
                    id="username"
                    name="username"
                    placeholder="הזן שם משתמש"
                    value={form.username}
                    onChange={handleChange}
                    disabled={loading}
                    autoComplete="username"
                    required
                  />
                </div>

                <div className="recipient-signup-field recipient-signup-field--full">
                  <label htmlFor="password">סיסמה</label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="הזן סיסמה"
                    value={form.password}
                    onChange={handleChange}
                    disabled={loading}
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>
            </section>

            {error && (
              <div className="recipient-signup-message error">
                {error}
              </div>
            )}

            <div className="recipient-signup-submit">
              <button type="submit" disabled={loading}>
                {loading ? "..." : "כניסה"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </section>
  );
};

export default Login;