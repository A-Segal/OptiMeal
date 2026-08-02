import React, { useEffect, useState } from "react";
import { base_url } from "../config";
import "../style/StaffHome.css";
import NavBar from "./NavBar";
import DownloadDividesButton from "./DownloadAssignmentsButton";

type StaffUser = {
  id: number;
  fname: string;
  lname: string;
  role: string;
  username: string;
  permission: string;
  mail: string;
  phone: string;
};

type MatchingResult = {
  created_count?: number;
};

type RunMatchingApiResponse = Partial<MatchingResult> & { message?: string; error?: string };

type DashboardServiceRow = {
  recipient_id: number;
  recipient_username: string | null;
  center_id: number | null;
  center_username: string | null;
  meals: number;
  address: string | null;
  source_address: string | null;
  request_date: string;
  service_date: string;
};

type DashboardSummary = {
  today_date: string;
  tomorrow_date: string;
  today_allocation: {
    successful_assignments: number;
    failed_assignments: number;
    status: string;
    total_requests: number;
  };
  tomorrow_allocation: {
    successful_assignments: number;
    failed_assignments: number;
    status: string;
    total_requests: number;
  };
  requests_for_today: DashboardServiceRow[];
  requests_for_tomorrow: DashboardServiceRow[];
  unassigned_today: DashboardServiceRow[];
  unassigned_tomorrow: DashboardServiceRow[];
  today_stats: {
    unassigned_requests: number;
    unassigned_meals: number;
  };
  tomorrow_stats: {
    unassigned_requests: number;
    unassigned_meals: number;
  };
  staff_overview: {
    secretaries: number;
    managers: number;
  };
};

type SystemUserRow = {
  id: number;
  user_type: string;
  role_label: string;
  username: string;
  full_name: string;
  mail?: string | null;
  phone?: string | null;
};

type NewUserForm = {
  fname: string;
  lname: string;
  username: string;
  password: string;
  mail: string;
  phone: string;
  roleType: "secretary" | "regular_user";
};

const STEPS = [
  "מנקה שיבוצים קודמים ומכין הרצה חדשה...",
  "מסנן רק בקשות של היום עבור משלוח מחר...",
  "מחשב התאמות בין מוטבים למרכזים...",
  "יוצר שיבוצי חלוקה ומשימות משלוח...",
  "מייצר דוח מסכם...",
];

const NAV_ITEMS = [
  { id: "tomorrow-requests", label: "שיבוץ למחר" },
  { id: "today-requests", label: "שיבוץ להיום" },
  { id: "new-user", label: "משתמש חדש" },
  { id: "user-management", label: "ניהול משתמשים" },
  { id: "smart-assignment-run", label: "הרצת שיבוץ" },
];

const EMPTY_NEW_USER_FORM: NewUserForm = {
  fname: "",
  lname: "",
  username: "",
  password: "",
  mail: "",
  phone: "",
  roleType: "secretary",
};

const StaffHome: React.FC = () => {
  const [user, setUser] = useState<StaffUser | null>(null);
  const [running, setRunning] = useState(false);
  const [progressText, setProgressText] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [matchingSummary, setMatchingSummary] = useState<MatchingResult | null>(null);
  const [resultErr, setResultErr] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [users, setUsers] = useState<SystemUserRow[]>([]);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [newUserForm, setNewUserForm] = useState<NewUserForm>(EMPTY_NEW_USER_FORM);
  const [newUserError, setNewUserError] = useState<string | null>(null);
  const [newUserSuccess, setNewUserSuccess] = useState<string | null>(null);

  const permissionValue = (user?.permission || "").toLowerCase();
  const isManager = permissionValue === "director" || permissionValue === "manager";
  const isSecretary = permissionValue === "מזכירות" || permissionValue === "secretary";

  useEffect(() => {
    const raw = localStorage.getItem("user");
    if (raw) {
      try {
        const p = JSON.parse(raw);
        if (p.role === "staff") setUser(p);
      } catch {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    if (!user) return;

    setActiveSection(null);
    setDashboard(null);
    setUsers([]);
    setUsersError(null);
    setMatchingSummary(null);
    setResultErr(null);

    void loadDashboard().catch(() => null);
    if ((user.permission || "").toLowerCase() === "director" || (user.permission || "").toLowerCase() === "manager") {
      void loadUsers().catch(() => null);
    }
  }, [user]);

  const loadDashboard = async () => {
    const res = await fetch(`${base_url}/staff/dashboard_summary`, {
      headers: { Accept: "application/json" },
    });

    if (!res.ok) throw new Error("Failed to load dashboard");

    const data = (await res.json()) as DashboardSummary;
    setDashboard(data);
  };

  const loadUsers = async () => {
    setUsersError(null);
    try {
      const res = await fetch(`${base_url}/staff/system_users`, {
        headers: { Accept: "application/json" },
      });

      if (!res.ok) throw new Error("Failed to load users");

      const data = (await res.json()) as SystemUserRow[];
      setUsers(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setUsersError(err.message || "שגיאה בטעינת משתמשים");
    }
  };

  const resetNewUserForm = () => {
    setNewUserForm(EMPTY_NEW_USER_FORM);
  };

  const submitNewUserForm = async () => {
    if (!isManager) return;

    setNewUserError(null);
    setNewUserSuccess(null);

    const payload = {
      fname: newUserForm.fname.trim(),
      lname: newUserForm.lname.trim(),
      username: newUserForm.username.trim(),
      password: newUserForm.password.trim(),
      mail: newUserForm.mail.trim(),
      phone: newUserForm.phone.trim(),
      role_type: newUserForm.roleType,
    };

    if (!payload.fname || !payload.lname || !payload.username || !payload.password) {
      setNewUserError("יש למלא את כל שדות החובה");
      return;
    }

    const res = await fetch(`${base_url}/staff/manager_create_user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Permission": user?.permission || "",
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setNewUserError((data as { error?: string }).error || "יצירת המשתמש נכשלה");
      return;
    }

    setNewUserSuccess("המשתמש נוצר בהצלחה");
    resetNewUserForm();
    await loadUsers();
  };

  const deleteUser = async (selectedUser: SystemUserRow) => {
    if (!isManager) return;

    const res = await fetch(`${base_url}/staff/system_users/${selectedUser.user_type}/${selectedUser.id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-User-Permission": user?.permission || "",
      },
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error((data as { error?: string }).error || "Delete failed");
    }

    await loadUsers();
  };

  const runMatching = async () => {
    if (running) return;

    setRunning(true);
    setMatchingSummary(null);
    setResultErr(null);
    setProgressStep(0);
    setProgressText(STEPS[0]);

    const intId = window.setInterval(() => {
      setProgressStep((prev) => {
        const next = (prev + 1) % STEPS.length;
        setProgressText(STEPS[next]);
        return next;
      });
    }, 1450);

    try {
      const res = await fetch(`${base_url}/delivery_assignment/run_matching`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data: RunMatchingApiResponse = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed");
      }

      setMatchingSummary({
        created_count: data.created_count ?? 0,
      });

      await loadDashboard();
    } catch (err: any) {
      setResultErr(err.message || "שגיאה בהרצת שיבוץ");
    } finally {
      window.clearInterval(intId);
      setProgressText(null);
      setRunning(false);
    }
  };

  if (!user) {
    return <div className="sh-page sh-page--admin"><NavBar alwaysSolid /><div className="sh-bg" /><div className="sh-admin-shell sh-admin-shell--empty"><div className="sh-admin-empty-card"><h1>אין גישה לדשבורד המזכירות</h1><p>יש להתחבר מחדש עם משתמש מורשה כדי להפעיל את מערכת השיבוץ.</p></div></div></div>;
  }

  const allowedSectionIds = isManager
    ? ["tomorrow-requests", "today-requests", "new-user", "user-management", "smart-assignment-run"]
    : isSecretary
      ? ["tomorrow-requests", "today-requests", "smart-assignment-run"]
      : ["today-requests", "tomorrow-requests"];
  const navItems = NAV_ITEMS.filter((item) => allowedSectionIds.includes(item.id));
  const userRoleLabel = isManager ? "מנהל מערכת" : isSecretary ? "מזכירות" : "איש צוות";

  const formatDate = (value?: string | null) => {
    if (!value) return "-";
    return new Date(value).toLocaleDateString("he-IL");
  };

  const todayAssignedRows = (dashboard?.requests_for_today ?? []).filter((row) => row.center_id != null);
  const tomorrowAssignedRows = (dashboard?.requests_for_tomorrow ?? []).filter((row) => row.center_id != null);

  return (
    <div className="sh-page sh-page--admin">
      <NavBar alwaysSolid />
      <div className="sh-bg" />

      <main className="sh-admin-shell">
        <div className="sh-admin-layout">
          <aside className="sh-admin-sidebar">
            <div className="sh-admin-userpanel">
              <span className="sh-admin-userpanel-role">{userRoleLabel}</span>
              <strong>{user.fname} {user.lname}</strong>
              <span>{user.username}</span>
            </div>

            <nav className="sh-admin-nav">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  className={`sh-admin-nav-item${activeSection === item.id ? " sh-admin-nav-item--active" : ""}`}
                  onClick={() => {
                    if (item.id === "user-management" && isManager && users.length === 0) {
                      void loadUsers();
                    }

                    if ((item.id === "today-requests" || item.id === "tomorrow-requests") && !dashboard) {
                      void loadDashboard();
                    }

                    setActiveSection(item.id);
                  }}
                >
                  {item.label}
                </button>
              ))}

              <div className="sh-admin-nav-actions">
                <DownloadDividesButton
                  className="sh-admin-nav-item"
                  disabled={!todayAssignedRows.length && !tomorrowAssignedRows.length}
                />
              </div>
            </nav>
          </aside>

          <section className="sh-admin-main">
              <>
            {running && progressText && (
              <div className="sh-progress-panel sh-admin-progress-panel">
                <div className="sh-progress-bar">
                  <div className="sh-progress-fill" style={{ width: `${((progressStep + 1) / STEPS.length) * 100}%` }} />
                </div>
                <p className="sh-progress-text">{progressText}</p>
              </div>
            )}

            {resultErr && <div className="sh-admin-alert">{resultErr}</div>}

            {activeSection === "smart-assignment-run" && (
              <section className="sh-admin-panel sh-admin-results">
                <div className="sh-admin-results-head">
                  <div>
                    <h2>הרצת שיבוץ</h2>
                    <p>הפעלת מערכת השיבוץ האוטומטית — התאמת מוטבים למרכזי חלוקה לפי קרבה גאוגרפית וכמות מנות.</p>
                  </div>
                </div>

                {matchingSummary && !running && (
                  <div className="sh-run-result">
                    <span className="sh-run-result-count">{matchingSummary.created_count ?? 0}</span>
                    <span>שיבוצים נוצרו בהצלחה</span>
                  </div>
                )}

                <div className="sh-admin-action-area">
                  <div className="sh-admin-action-copy">
                    <h3>הפעלת שיבוץ</h3>
                    <p>לחיצה על הכפתור תתחיל תהליך התאמה אוטומטי בין מוטבים למרכזי חלוקה.</p>
                  </div>
                  <button className="sh-admin-run sh-admin-run--primary" onClick={() => void runMatching()} disabled={running}>
                    {running ? "משבץ..." : "הרץ שיבוץ"}
                  </button>
                </div>
              </section>
            )}

            {activeSection === "today-requests" && (
              <section className="sh-admin-panel sh-admin-results">
                <div className="sh-admin-results-head">
                  <div>
                    <h2>שיבוץ להיום</h2>
                    <p>שיבוצים שהוקצו עבור היום — {formatDate(dashboard?.today_date)}</p>
                  </div>
                  <div className="sh-admin-results-meta">
                    <span>סה״כ שובצו: {todayAssignedRows.length}</span>
                    <span>סך מנות: {todayAssignedRows.reduce((sum, row) => sum + row.meals, 0)}</span>
                  </div>
                </div>

                <div className="sh-table-scroll sh-admin-table-scroll">
                  <table className="sh-table sh-admin-table">
                    <thead>
                      <tr>
                        <th>מוטב</th>
                        <th>מרכז חלוקה</th>
                        <th>מנות</th>
                        <th>כתובת מוצא</th>
                        <th>כתובת יעד</th>
                        <th>תאריך שירות</th>
                      </tr>
                    </thead>
                    <tbody>
                      {todayAssignedRows.length ? todayAssignedRows.map((row) => (
                        <tr key={`today-${row.recipient_id}-${row.request_date}`}>
                          <td>{row.recipient_username || `user_${row.recipient_id}`}</td>
                          <td>{row.center_username || "-"}</td>
                          <td>{row.meals}</td>
                          <td>{row.source_address || "-"}</td>
                          <td>{row.address || "-"}</td>
                          <td>{formatDate(row.service_date)}</td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={6} className="sh-admin-empty-row">אין שיבוצים שהוקצו להיום</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {activeSection === "tomorrow-requests" && (
              <section className="sh-admin-panel sh-admin-results">
                <div className="sh-admin-results-head">
                  <div>
                    <h2>שיבוץ למחר</h2>
                    <p>שיבוצים מתוכננים למחר — {formatDate(dashboard?.tomorrow_date)}</p>
                  </div>
                  <div className="sh-admin-results-meta">
                    <span>סה״כ שובצו: {tomorrowAssignedRows.length}</span>
                    <span>סך מנות: {tomorrowAssignedRows.reduce((sum, row) => sum + row.meals, 0)}</span>
                  </div>
                </div>

                <div className="sh-table-scroll sh-admin-table-scroll">
                  <table className="sh-table sh-admin-table">
                    <thead>
                      <tr>
                        <th>מוטב</th>
                        <th>מרכז חלוקה</th>
                        <th>מנות</th>
                        <th>כתובת מוצא</th>
                        <th>כתובת יעד</th>
                        <th>תאריך שירות</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tomorrowAssignedRows.length ? tomorrowAssignedRows.map((row) => (
                        <tr key={`tomorrow-${row.recipient_id}-${row.request_date}`}>
                          <td>{row.recipient_username || `user_${row.recipient_id}`}</td>
                          <td>{row.center_username || "-"}</td>
                          <td>{row.meals}</td>
                          <td>{row.source_address || "-"}</td>
                          <td>{row.address || "-"}</td>
                          <td>{formatDate(row.service_date)}</td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={6} className="sh-admin-empty-row">אין שיבוצים מתוכננים למחר</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {activeSection === "user-management" && isManager && (
              <section className="sh-admin-panel sh-admin-results">
                <div className="sh-admin-results-head">
                  <div>
                    <h2>ניהול משתמשים</h2>
                    <p>
                      למנהל בלבד: צפייה בכל משתמשי המערכת ומחיקה לפי הרשאה.
                    </p>
                  </div>
                  <div className="sh-admin-results-meta">
                    <span>מזכירות: {dashboard?.staff_overview.secretaries ?? 0}</span>
                    <span>מנהלים: {dashboard?.staff_overview.managers ?? 0}</span>
                  </div>
                </div>

                {usersError ? <div className="sh-admin-alert">{usersError}</div> : null}

                <div className="sh-table-scroll sh-admin-table-scroll">
                  <table className="sh-table sh-admin-table">
                    <thead>
                      <tr>
                        <th>שם משתמש</th>
                        <th>שם מלא</th>
                        <th>תפקיד</th>
                        <th>אימייל</th>
                        <th>טלפון</th>
                        <th>פעולה</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.length ? users.map((systemUser) => (
                        <tr key={`${systemUser.user_type}-${systemUser.id}`}>
                          <td>{systemUser.username}</td>
                          <td>{systemUser.full_name}</td>
                          <td>{systemUser.role_label}</td>
                          <td>{systemUser.mail || "-"}</td>
                          <td>{systemUser.phone || "-"}</td>
                          <td>
                            <button
                              className="sh-admin-delete"
                              onClick={() => {
                                void deleteUser(systemUser).catch((err: any) => setUsersError(err.message || "מחיקה נכשלה"));
                              }}
                            >
                              מחק
                            </button>
                          </td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={6} className="sh-admin-empty-row">אין משתמשים להצגה</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {activeSection === "new-user" && isManager && (
              <section className="sh-admin-panel sh-admin-results">
                <div className="sh-admin-results-head">
                  <div>
                    <h2>משתמש חדש</h2>
                  </div>
                </div>

                <div className="sh-admin-form-grid">
                  <label className="sh-admin-form-field">
                    <span>שם פרטי</span>
                    <input
                      value={newUserForm.fname}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, fname: e.target.value }))}
                      placeholder="הזן שם פרטי"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>שם משפחה</span>
                    <input
                      value={newUserForm.lname}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, lname: e.target.value }))}
                      placeholder="הזן שם משפחה"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>שם משתמש</span>
                    <input
                      value={newUserForm.username}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, username: e.target.value }))}
                      placeholder="הזן שם משתמש"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>סיסמה</span>
                    <input
                      type="password"
                      value={newUserForm.password}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, password: e.target.value }))}
                      placeholder="הזן סיסמה"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>אימייל</span>
                    <input
                      type="email"
                      value={newUserForm.mail}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, mail: e.target.value }))}
                      placeholder="הזן אימייל"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>טלפון</span>
                    <input
                      type="tel"
                      value={newUserForm.phone}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, phone: e.target.value }))}
                      placeholder="הזן טלפון"
                    />
                  </label>

                  <label className="sh-admin-form-field">
                    <span>תפקיד משתמש</span>
                    <select
                      value={newUserForm.roleType}
                      onChange={(e) => setNewUserForm((prev) => ({ ...prev, roleType: e.target.value as "secretary" | "regular_user" }))}
                    >
                      <option value="secretary">מזכירות</option>
                      <option value="regular_user">משתמש רגיל</option>
                    </select>
                  </label>
                </div>

                <div className="sh-admin-form-actions">
                  <button className="sh-admin-run" onClick={() => void submitNewUserForm()}>צור משתמש</button>
                  <button className="sh-admin-reset" onClick={resetNewUserForm}>נקה</button>
                </div>

                {newUserError ? <div className="sh-admin-alert">{newUserError}</div> : null}
                {newUserSuccess ? <div className="sh-admin-success">{newUserSuccess}</div> : null}
              </section>
            )}
              </>
          </section>
        </div>
      </main>
    </div>
  );
};

export default StaffHome;
