import "../style/EzerMizionStyleGuide.css";

function EzerMizionStyleGuide() {
  return (
    <div className="ez-page" dir="ltr">
      <header className="ez-hero">
        <p className="ez-kicker">Cloud Build Reference</p>
        <h1>Ezer Mizion Website Recreation Guide</h1>
        <p className="ez-subtitle">
          This page documents the target structure, visual language, and implementation rules
          for recreating an "Ezer Mizion-like" nonprofit website style in this project, even
          when cloud tooling cannot access the real website directly.
        </p>
      </header>

      <main className="ez-content">
        <section className="ez-card">
          <h2>1) Project Goal</h2>
          <p>
            Build a trustworthy, clean, nonprofit-style web experience with clear calls to action,
            high readability, and warm community-oriented tone.
          </p>
          <ul>
            <li>Keep layouts simple, structured, and scannable.</li>
            <li>Prioritize support/help messaging over marketing-heavy language.</li>
            <li>Ensure accessibility and responsive behavior from the start.</li>
          </ul>
        </section>

        <section className="ez-card">
          <h2>2) Site Map and Main Views</h2>
          <div className="ez-grid two">
            <article>
              <h3>Core Pages</h3>
              <ul>
                <li>Home (hero + services + impact + call to action)</li>
                <li>About organization</li>
                <li>Programs or services listing</li>
                <li>Request help / registration forms</li>
                <li>Donate / support flow</li>
                <li>Contact page</li>
                <li>Legal utility pages (privacy, accessibility, terms)</li>
              </ul>
            </article>
            <article>
              <h3>User Views in This Project</h3>
              <ul>
                <li>Volunteer view</li>
                <li>Recipient view</li>
                <li>Distribution center view</li>
                <li>Staff view</li>
              </ul>
            </article>
          </div>
        </section>

        <section className="ez-card">
          <h2>3) Global Layout Blueprint</h2>
          <ol>
            <li>Top header with logo, main nav, and a primary CTA button.</li>
            <li>Hero area with clear headline and one dominant action.</li>
            <li>Service cards section in 2-4 columns on desktop, 1 column on mobile.</li>
            <li>Impact or trust section (numbers, testimonials, mission statements).</li>
            <li>Secondary CTA band between informational sections.</li>
            <li>Contact/lead form block with concise labels and validation.</li>
            <li>Footer with grouped links, contact info, and legal links.</li>
          </ol>
        </section>

        <section className="ez-card">
          <h2>4) Visual Style System</h2>
          <div className="ez-grid two">
            <article>
              <h3>Design Direction</h3>
              <ul>
                <li>Nonprofit trust aesthetic: clean, friendly, practical.</li>
                <li>Avoid cluttered layouts or aggressive animations.</li>
                <li>Use section alternation for rhythm and readability.</li>
                <li>Cards and containers with soft corners and subtle depth.</li>
              </ul>
            </article>
            <article>
              <h3>Spacing Scale</h3>
              <ul>
                <li>Base unit: 8px</li>
                <li>Component paddings: 16 / 24 / 32</li>
                <li>Section spacing: 48 to 88</li>
                <li>Content max width: 1120 to 1240px</li>
              </ul>
            </article>
          </div>
        </section>

        <section className="ez-card">
          <h2>5) Colors (Design Tokens)</h2>
          <p>Use CSS variables and keep usage consistent across all views.</p>
          <pre className="ez-code">
{`:root {
  --color-primary: #0b5d57;
  --color-primary-strong: #08453f;
  --color-secondary: #1f7a8c;
  --color-accent: #f2c14e;
  --color-bg: #f8fbfa;
  --color-surface: #ffffff;
  --color-text: #1f2933;
  --color-text-soft: #52606d;
  --color-border: #d9e2ec;
  --color-success: #2d9d78;
  --color-error: #d64545;
}`}
          </pre>
          <ul>
            <li>Primary: navigation, important headings, primary buttons.</li>
            <li>Accent: highlight key actions or impact numbers only.</li>
            <li>Neutrals: body text, borders, low-emphasis surfaces.</li>
          </ul>
        </section>

        <section className="ez-card">
          <h2>6) Fonts and Typography</h2>
          <ul>
            <li>Prefer Hebrew-friendly sans fonts with strong readability.</li>
            <li>Fallback stack suggestion: "Heebo", "Rubik", "Assistant", sans-serif.</li>
            <li>H1: 2.0rem to 2.8rem, bold, tight line-height.</li>
            <li>H2: 1.5rem to 2rem, semibold to bold.</li>
            <li>Body: 1rem to 1.125rem with 1.6 line-height.</li>
            <li>Buttons: medium to semibold, clear contrast.</li>
          </ul>
        </section>

        <section className="ez-card">
          <h2>7) HTML and Component Structure</h2>
          <p>Use semantic HTML and reusable React components.</p>
          <pre className="ez-code">
{`<header>...</header>
<main>
  <section class="hero">...</section>
  <section class="services-grid">...</section>
  <section class="impact">...</section>
  <section class="cta-band">...</section>
  <section class="form-section">...</section>
</main>
<footer>...</footer>`}
          </pre>
          <ul>
            <li>Use landmarks: header, nav, main, section, article, footer.</li>
            <li>Create shared components: SectionTitle, ServiceCard, CTAButton, FormField.</li>
            <li>Keep class naming consistent and descriptive.</li>
          </ul>
        </section>

        <section className="ez-card">
          <h2>8) Interaction and UX Rules</h2>
          <ul>
            <li>Primary CTA should remain visible in header and key sections.</li>
            <li>Hover states: slight lift or color darken, no distracting effects.</li>
            <li>Form UX: inline validation, clear error messages, short labels.</li>
            <li>Animations: subtle fade/slide-in for section entry, 200-350ms.</li>
          </ul>
        </section>

        <section className="ez-card">
          <h2>9) Accessibility and Responsiveness</h2>
          <ul>
            <li>Keyboard navigable controls and visible focus rings.</li>
            <li>Contrast must pass WCAG-friendly thresholds.</li>
            <li>Alt text for meaningful imagery.</li>
            <li>Mobile-first breakpoints and readable line lengths.</li>
            <li>Touch targets at least 44x44 for key actions.</li>
          </ul>
        </section>

        <section className="ez-card ez-final">
          <h2>10) Cloud Instruction (Copy to AI Builder)</h2>
          <pre className="ez-code">
{`Recreate this project UI in an Ezer Mizion-style nonprofit visual language.
Follow the structure and tokens in this guide exactly.
Use semantic HTML, accessible forms, clear CTA hierarchy,
responsive sections, and consistent typography.
Do not invent an unrelated design direction.`}
          </pre>
          <p>
            This page exists to provide a direct on-project reference when external site access is
            blocked in cloud environments.
          </p>
        </section>
      </main>
    </div>
  );
}

export default EzerMizionStyleGuide;
