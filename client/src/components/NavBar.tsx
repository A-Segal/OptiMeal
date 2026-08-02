import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

interface NavBarProps {
  /** If true, shows the "solid" scrolled style by default (for pages that aren't at the top) */
  alwaysSolid?: boolean;
  /** If true, applies the homepage-only navigation look */
  homePage?: boolean;
}
/** Shared navigation bar used across all pages */
const NavBar: React.FC<NavBarProps> = ({ alwaysSolid = false, homePage = false }) => {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [messageIndex, setMessageIndex] = useState(0);
  const [regOpen, setRegOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  const speakerMessages = useMemo(
    () => [
      "התאמה חכמה בין מרכזי החלוקה למשפחות הזקוקות לסיוע.",
      "כל בקשה משויכת אוטומטית למרכז החלוקה המתאים ביותר.",
      "המערכת מחשבת את מרכז החלוקה האופטימלי לכל משלוח.",
      "התאמה מדויקת שמקצרת מרחקים ומייעלת את החלוקה.",
      "כל מסלול מחושב באופן אוטומטי לקבלת היעילות המרבית.",
      "מסלולים חכמים שחוסכים זמן ומאפשרים להגיע ליותר משפחות.",
      "כל מסלול מותאם לפי המרחק, זמינות המתנדב וקיבולת הרכב.",
      "המערכת בונה לכל מתנדב את המסלול האופטימלי.",
      "פחות נסיעות מיותרות, יותר משלוחים מוצלחים.",
      "שיבוץ המתנדבים מתבצע בהתאם לזמינות שלהם.",
      "המערכת מתחשבת בקיבולת הרכב של כל מתנדב.",
      "כל שיבוץ נבנה לפי זמן, מרחק ויכולת ההובלה.",
      "האלגוריתם מאזן בין עומס, מרחק וזמינות.",
      "כל מתנדב מקבל מסלול שמתאים בדיוק ליכולותיו.",
      "תכנון חכם שמפחית זמני נסיעה ומגדיל את מספר המשלוחים.",
      "אופטימיזציה חכמה לכל שלב בתהליך החלוקה.",
      "פחות זמן על הכביש, יותר משפחות שמקבלות סיוע.",
      "כל החלטה מבוססת על חישוב אופטימלי.",
      "המערכת מאזנת בין מרחק, זמן, עומס וקיבולת לקבלת תוצאה מיטבית.",
    ],
    []
  );
  const user = (() => {
    try { return JSON.parse(localStorage.getItem("user") || "{}"); }
    catch { return {}; }
  })();

  useEffect(() => {
    if (alwaysSolid) {
      return;
    }

    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, [alwaysSolid]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % speakerMessages.length);
    }, 9800);

    return () => window.clearInterval(interval);
  }, [speakerMessages]);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setRegOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  const currentMessage = speakerMessages[messageIndex] || "";
  const isSolid = alwaysSolid || scrolled;
  const logoSrc = "/optimeal.png";

  const navClass = `home-nav${isSolid ? " nav-solid" : ""}${homePage ? " home-nav--home" : ""}`;
  const logoClass = "home-nav-logo-svg home-nav-logo-svg--optimeal";

  return (
    <nav className={navClass}>
      <div className="home-nav-inner">
        <div className="home-nav-actions" dir="rtl">
          <Link to="/">דף הבית</Link>

          {!user?.role && (
            <div className="nav-dropdown" ref={dropdownRef}>
              <button
                className="nav-link-btn nav-reg-btn"
                onClick={() => setRegOpen((open) => !open)}
                aria-expanded={regOpen}
                type="button"
              >
                הרשמה
                <span className={`nav-chevron ${regOpen ? "open" : ""}`}>▾</span>
              </button>
              {regOpen && (
                <div className="nav-dropdown-menu">
                  <Link to="/volunteerSignUp" className="nav-dropdown-item" onClick={() => setRegOpen(false)}>
                    <span>
                      <strong>מתנדבים</strong>
                      <small>הצטרפו למערך השליחים</small>
                    </span>
                  </Link>
                  <Link to="/RecipientSignUp" className="nav-dropdown-item" onClick={() => setRegOpen(false)}>
                    <span>
                      <strong>מקבלי סיוע</strong>
                      <small>הרשמה לקבלת ארוחות חמות</small>
                    </span>
                  </Link>
                  <Link to="/DistributionCenterSignUp" className="nav-dropdown-item" onClick={() => setRegOpen(false)}>
                    <span>
                      <strong>מרכזי חלוקה</strong>
                      <small>ניהול הכנת הארוחות ונקודות החלוקה</small>
                    </span>
                  </Link>
                </div>
              )}
            </div>
          )}
          {user?.role === "volunteer" && <Link to="/volunteer-home">המסלול שלי</Link>}
          {user?.role === "recipient" && <Link to="/recipient-home">האזור שלי</Link>}
          {user?.role === "distribution_center" && <Link to="/dc-home">ניהול מרכז</Link>}
          {user?.role === "staff" && <Link to="/staff-home">ניהול מערכת</Link>}

          {user?.role ? (
            <button className="nav-link-btn nav-login-btn" onClick={handleLogout}>
              התנתקות
            </button>
          ) : (
            <Link to="/login" className="nav-link-btn nav-login-btn">התחברות</Link>
          )}
        </div>

        <div className="home-nav-speaker" dir="rtl" aria-live="polite">
          <img src="/speaker.png" className="home-nav-source-icon" alt="מקור הודעה" />
          <div className="home-nav-message-lane">
            <span key={messageIndex} className="home-nav-message-fly">
              {currentMessage}
            </span>
          </div>
          <img src="/ico_pause.svg" className="home-nav-target-icon" alt="סיום הודעה" />
        </div>

        <div className="home-nav-brand" dir="rtl">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <img src={logoSrc} className={logoClass} alt="OptiMeal" />
            <span className="home-nav-brand-text">OptiMeal</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavBar;
