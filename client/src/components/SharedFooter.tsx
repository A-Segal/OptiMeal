import React, { useEffect, useState } from "react";
import { base_url } from "../config";

type StaffContact = {
  id: number;
  fname: string;
  lname: string;
  mail?: string;
  phone?: string;
  PermissionID?: number;
};

const SharedFooter: React.FC = () => {
  const [staff, setStaff] = useState<StaffContact[]>([]);

  useEffect(() => {
    let cancelled = false;

    const loadContacts = async () => {
      try {
        const response = await fetch(`${base_url}/staff`, { headers: { Accept: "application/json" } });
        if (!response.ok) return;
        const data = (await response.json()) as StaffContact[];
        if (!cancelled) setStaff(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setStaff([]);
      }
    };

    loadContacts();

    return () => {
      cancelled = true;
    };
  }, []);

  const secretariat = staff.find((member) => member.PermissionID !== 1);
  const management = staff.find((member) => member.PermissionID === 1);

  const renderContact = (member?: StaffContact, fallbackLabel = "אין פרטים כרגע") => {
    if (!member) {
      return <div className="home-footer-contact-lines">{fallbackLabel}</div>;
    }

    return (
      <div className="home-footer-contact-lines">
        <strong>{`${member.fname || ""} ${member.lname || ""}`.trim() || fallbackLabel}</strong>
        {member.phone && <span>טלפון: {member.phone}</span>}
        {member.mail && <span>מייל: {member.mail}</span>}
      </div>
    );
  };

  return (
    <footer className="home-footer home-footer--shared">
      <div className="home-footer-content home-footer-content--large">
        <div className="home-footer-brand-wrap home-footer-brand-wrap--large">
          <img src="/hand.svg" className="home-footer-hand" alt="עזר מציון" />
          <div>
            <div className="home-footer-brand-title">עזר מציון</div>
            <div className="home-footer-brand-subtitle">מערכת חכמה לניהול משלוחים</div>
          </div>
        </div>

        <div className="home-footer-help-block">
          <div className="home-footer-help-title">צריך עזרה? אנחנו פה</div>
          <div className="home-footer-help-grid">
            <div className="home-footer-help-card">
              <span className="home-footer-help-label">מזכירות</span>
              {renderContact(secretariat, "פרטי המזכירות לא עודכנו")}
            </div>
            <div className="home-footer-help-card">
              <span className="home-footer-help-label">הנהלה</span>
              {renderContact(management, "פרטי ההנהלה לא עודכנו")}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default SharedFooter;