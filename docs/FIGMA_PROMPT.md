# Figma AI — UI/UX Design Prompt
# Soite Kotikuntoutus Feedback System

---

## PROJECT CONTEXT

Design a **patient feedback kiosk application** for Soite's home rehabilitation team in Kokkola, Finland. The app runs on Android tablets left in patients' homes. Patients are typically 50–85 years old, post-surgery, with varying digital literacy. The UI must be extremely simple, calming, and accessible.

There are three distinct screens/user types to design:

1. **Kiosk View** — anonymous patient-facing tablet UI
2. **Staff Dashboard** — authenticated staff view (aggregate charts)
3. **Admin Panel** — question management for team lead

---

## SCREEN 1: KIOSK — PATIENT VIEW

### Design principles
- One question per screen — never show more than one question at a time
- Giant touch targets — minimum 80px height for any tappable element
- No text input by default — emoji/icon-based answers preferred
- Calm, healthcare-appropriate color palette — soft blues and whites, no harsh reds
- Finnish language only on this screen
- Progress shown as simple dots (e.g. ● ● ○ ○ ○), not numbers
- Auto-reset after thank-you screen (10-second countdown visible)

### Screens to design

**1a. Welcome screen**
- Soite logo top-left
- Large friendly illustration or icon (hand-shake or heart)
- Heading: "Hei! Haluatko antaa palautetta?" (32px minimum)
- Single large CTA button: "Aloita kysely →" (green, full-width, 80px height)
- Small text: "Kysely on täysin anonyymi ja kestää noin 1 minuutin"

**1b. Scale question screen (5-point emoji scale)**
- Progress dots at top
- Question text: large, centered, bold (28px minimum)
  Example: "Kuinka tyytyväinen olit saamaasi hoitoon?"
- 5 emoji/icon buttons in a row:
  😞 😕 😐 🙂 😄
  (Very unhappy → Very happy)
- Labels below each: "Erittäin tyytymätön" ... "Erittäin tyytyväinen"
- No "Next" button — tapping an emoji advances automatically
- Selected state: emoji scales up slightly, card highlights

**1c. Yes/No question screen**
- Progress dots at top
- Question text large and centered
  Example: "Saitko riittävästi tietoa kuntoutuksestasi?"
- Two large buttons, full-width, stacked:
  ✓ Kyllä (green background, 100px height)
  ✗ En (light gray background, 100px height)

**1d. Optional free-text screen**
- Progress dots at top
- Question: "Haluatko antaa muuta palautetta?" (optional)
- Large textarea (min 200px height, 20px font)
- Placeholder: "Kirjoita halutessasi..."
- Character counter: "0 / 500"
- Two buttons: "Ohita" (skip, text-only) | "Lähetä palaute →" (primary)

**1e. Thank-you screen**
- Large checkmark animation (green circle with ✓)
- Heading: "Kiitos palautteestasi!" (36px)
- Subtext: "Palautteesi auttaa meitä kehittämään palveluamme."
- Countdown: "Näyttö nollautuu 10 sekunnin kuluttua..." (small, bottom)
- Progress bar depleting at bottom

### Color palette (kiosk)
- Background: #F7F9FC (near white, warm)
- Primary action: #2D7D9A (calm teal-blue)
- Secondary: #F0F4F8
- Success/Yes: #3D9A6A (soft green)
- Text primary: #1A2332
- Emoji scale 1: #E85D4A, 2: #F0934E, 3: #F5C842, 4: #8BC34A, 5: #4CAF50

### Typography
- Font: System UI or Inter (high legibility)
- Question text: 28–32px, weight 600
- Body/labels: 18–20px, weight 400
- Button text: 22px, weight 600
- All text: high contrast (WCAG AA minimum)

---

## SCREEN 2: STAFF DASHBOARD

### Design principles
- Clean data dashboard aesthetic
- Finnish + English labels
- Accessible color palette (not relying on color alone)
- Sidebar navigation: Overview | Free-text responses | Export

### Screens to design

**2a. Overview dashboard**
- Top bar: Soite logo + "Kotikuntoutus — Palautepaneeli" + logout button
- Date range picker (this week / this month / custom)
- Stats row: Total responses | This week | Average satisfaction score
- Per-question cards:
  - Scale questions: horizontal bar chart (5 bars, emoji labels)
  - Yes/No questions: donut chart (Yes % vs No %)
  - Text questions: "12 vapaamuotoista vastausta →" (link to 2b)

**2b. Free-text responses view**
- Table/list: one response per row
- No metadata shown (no date, no device — privacy)
- Pagination: 20 per page
- Filter by question dropdown

**2c. Export page (admin only)**
- Date range selector
- Format: CSV
- Warning notice: "Tiedosto sisältää anonymisoitua dataa."
- Download button

### Color palette (dashboard)
- Background: #FFFFFF / #F8FAFC
- Sidebar: #1E2A3A (dark navy)
- Sidebar text: #E8EDF2
- Primary accent: #2D7D9A
- Chart colors: Use a colorblind-safe 5-color palette
- Cards: white with subtle shadow

---

## SCREEN 3: ADMIN PANEL

### Screens to design

**3a. Question management**
- Table of all questions (active + inactive)
- Columns: Order | Finnish text | Type | Status | Actions
- Drag handle for reordering
- Toggle switch for active/inactive
- "Add question" button → opens modal

**3b. Add/edit question modal**
- Fields: Finnish text (required), English text (optional), Type (dropdown), Order
- Preview: "Preview in kiosk →" button
- Save / Cancel

**3c. User management**
- Table: Email | Role | Last login | Status
- "Add staff user" button
- Deactivate button (no delete)

---

## DESIGN SYSTEM REQUIREMENTS

- Create a shared component library with:
  - Button variants: Primary, Secondary, Destructive, Ghost
  - Input fields with error states
  - Toggle switch
  - Progress dots
  - Chart components
  - Card component
  - Modal/dialog
  - Toast notifications

- Design for **tablet landscape** (1024×768) for kiosk screens
- Design for **desktop** (1440×900) for dashboard and admin screens
- Include dark mode variant for dashboard only (kiosk stays light)
- Export all assets at 2x for retina displays

---

## ACCESSIBILITY REQUIREMENTS

- All interactive elements: minimum 44×44px touch target (80px preferred on kiosk)
- Color contrast: WCAG AA minimum (4.5:1 for normal text, 3:1 for large text)
- Focus indicators: visible 3px outline on all focusable elements
- No information conveyed by color alone (always pair with icon or text)
- Screen reader-friendly: proper heading hierarchy, ARIA labels on icon buttons
- Reduce motion: no auto-playing animations that cannot be paused
