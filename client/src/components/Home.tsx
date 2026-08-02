import { useState, useRef, useEffect } from "react";
import NavBar from "./NavBar";
import "../style/Home.css";

function Home() {
  const [flowOpen, setFlowOpen] = useState(false);
  const [countersStarted, setCountersStarted] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);

  // parallax on hero
  useEffect(() => {
    const onScroll = () => {
      if (heroRef.current) {
        const s = window.scrollY;
        heroRef.current.style.setProperty("--scroll", String(s));
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setCountersStarted(true);
        }
      },
      { threshold: 0.45 }
    );

    if (statsRef.current) {
      obs.observe(statsRef.current);
    }

    return () => obs.disconnect();
  }, []);

  const closeFlow = () => setFlowOpen(false);

  return (
    <div className="home-page">
      {/* ===== NAV BAR ===== */}
      <NavBar alwaysSolid homePage />

      {/* ===== HERO ===== */}
      <section className="home-hero" ref={heroRef}>
        <div className="home-hero-bg" />

        <div className="home-hero-content">
          <img src="/optimeal.png" alt="OptiMeal" className="home-hero-coin" />

          <div className="home-hero-copy-shell">
            <h1 className="home-hero-copy-title">המערכת החכמה לחלוקה מדויקת</h1>
            <p className="home-hero-copy-subtitle">שיבוץ מהיר, תיאום ברור, תוצאה מדויקת.</p>
          </div>
        </div>

      </section>

      {/* ===== FEATURES ===== */}
      <section className="home-features" id="home-features">
        <div className="section-header">
          <h2 className="section-title reveal-up delay-1">שיבוץ חכם פשוט בשלבים</h2>
        </div>

        <div className="home-process-timeline" aria-label="תהליך שיבוץ">
          <article className="home-process-step delay-1">
            <span className="home-process-step-num">1</span>
            <h3>קליטת בקשות</h3>
            <p>המערכת מרכזת את בקשות הסיוע ומכינה נתונים לשיבוץ.</p>
          </article>

          <article className="home-process-step delay-2">
            <span className="home-process-step-num">2</span>
            <h3>התאמה חכמה</h3>
            <p>מבוצעת התאמה אופטימלית בין מרכזים, זמינות וכתובות.</p>
          </article>

          <article className="home-process-step delay-3">
            <span className="home-process-step-num">3</span>
            <h3>ביצוע ומעקב</h3>
            <p>השיבוץ יוצא לדרך עם סטטוס ברור ועדכונים רציפים לצוות.</p>
          </article>
        </div>
      </section>

      {/* ===== STATS ===== */}
      <section className="home-stats home-stats--home" id="home-stats" ref={statsRef}>
        <div className="stats-bg-pattern"></div>
        <div className="home-stats-inner">
          <CounterItem end={120} label="מרכזי חלוקה" suffix="+" started={countersStarted} />
          <div className="stat-divider"></div>
          <CounterItem end={3500} label="מתנדבים פעילים" suffix="+" started={countersStarted} />
          <div className="stat-divider"></div>
          <CounterItem end={8000} label="ארוחות בכל שבוע" suffix="+" started={countersStarted} />
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="home-footer home-footer--home">
        <div className="footer-bottom">
          <p>© 2026 עזר מציון — מערך משלוחי המזון. כל הזכויות שמורות.</p>
          <p className="home-footer-small">בסיוע אלפי מתנדבים ומרכזי חלוקה ברחבי הארץ</p>
        </div>
      </footer>

      {flowOpen ? (
        <div className="flow-modal-backdrop" role="dialog" aria-modal="true" aria-label="איך המערכת עובדת">
          <div className="flow-modal">
            <button type="button" className="flow-modal-close" onClick={closeFlow} aria-label="סגירה">×</button>
            <div className="flow-modal-header">
              <span className="section-tag">איך המערכת עובדת</span>
              <h2>כך המערכת עובדת</h2>
              <p>
                OptiMeal קולטת בקשות, מתאימה למרכזים, מייצרת שיבוץ ומציגה סטטוסים בזמן אמת.
              </p>
            </div>
            <div className="flow-steps">
              <div className="flow-step"><strong>1</strong><span>הזנת בקשות ופרטי משתמשים</span></div>
              <div className="flow-step"><strong>2</strong><span>התאמה חכמה למרכזים ומשאבים</span></div>
              <div className="flow-step"><strong>3</strong><span>שיבוץ, ניהול ומעקב בזמן אמת</span></div>
            </div>
          </div>
        </div>
      ) : null}

    </div>
  );
}

function CounterItem({ end, label, suffix, started }: { end: number; label: string; suffix: string; started: boolean }) {
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!started) return;

    const duration = 1800;
    const steps = 60;
    const stepTime = duration / steps;
    let frame = 0;

    const timer = window.setInterval(() => {
      frame += 1;
      const progress = frame / steps;
      const eased = 1 - Math.pow(1 - progress, 3);
      setVal(Math.round(end * eased));

      if (frame >= steps) {
        window.clearInterval(timer);
      }
    }, stepTime);

    return () => window.clearInterval(timer);
  }, [end, started]);

  return (
    <div className="stat-item">
      <span className="stat-number">{val.toLocaleString()}{suffix}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export default Home;
