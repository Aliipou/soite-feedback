# PRD — Soite Kotikuntoutus Feedback System
**Version**: 1.0.0  
**Status**: Approved  
**Owner**: Ali Pourrahim (Centria UAS)  
**Stakeholder**: Anu Kamau (anu.kamau@centria.fi), Minna LillKåla (minna.lillkala@soite.fi)  
**Last updated**: 2026-05-17

---

## 1. Problem statement

Soite's home rehabilitation team (kotikuntoutus) visits 1–4 patients/day, each for 1–4 weeks post-surgery or post-operation. Previously, paper feedback forms left at the patient's home produced **100+ responses/year**. After migrating to a web form on soite.fi, responses dropped to **2/year** — a 98% collapse.

The team lead has long requested a kiosk-style device (similar to smiley-face terminals in retail) but none has been provided.

**Root cause**: friction. Patients do not navigate to soite.fi on their own initiative. A tablet left in the room, showing one question at a time, removes all friction.

---

## 2. Goals

| Goal | Metric | Target |
|------|--------|--------|
| Restore response volume | Responses/year | ≥ 80 in first 6 months |
| Reduce staff overhead | Minutes to review weekly summary | ≤ 5 min |
| Accessible to all patients | WCAG level | 2.1 AA |
| GDPR compliant | PII in database | Zero |
| Deployable on HealthLab tablets | Platform | PWA on Chrome/Android tablet |

---

## 3. User personas

### 3.1 Potilas (Patient) — primary user of kiosk
- Post-surgery, 50–85 years old
- May have limited motor dexterity, vision impairment, low digital literacy
- Uses the app once per rehabilitation visit, for 60–90 seconds
- Never creates an account; completely anonymous

### 3.2 Hoitaja (Care worker) — staff dashboard user
- Reads weekly summary of responses
- Does not need per-response detail; aggregate charts are sufficient
- Accesses via personal tablet or browser with credentials

### 3.3 Admin (Team lead / Minna LillKåla)
- Manages survey questions (add, edit, reorder, deactivate)
- Exports data as CSV or PDF for reporting
- Receives weekly automated summary email

---

## 4. Functional requirements

### 4.1 Kiosk / Patient view (anonymous, no login)
- **FR-K1**: Display one question at a time in large Finnish text (min 24px)
- **FR-K2**: Answer types: 5-point emoji scale, yes/no, optional free text (max 500 chars)
- **FR-K3**: Progress indicator (e.g. "Kysymys 2/5")
- **FR-K4**: Thank-you screen with auto-reset after 10 seconds
- **FR-K5**: Works offline (PWA service worker caches questions); syncs on reconnect
- **FR-K6**: No back-navigation once submission is confirmed
- **FR-K7**: Session token generated per device boot (random UUID, not tied to patient)

### 4.2 Staff dashboard (JWT authenticated)
- **FR-D1**: Overview: total responses this week/month/all-time
- **FR-D2**: Per-question breakdown: bar chart + emoji distribution
- **FR-D3**: Free-text responses listed chronologically (no metadata shown)
- **FR-D4**: Date range filter
- **FR-D5**: Export to CSV (admin only)

### 4.3 Admin panel (elevated JWT role)
- **FR-A1**: CRUD for survey questions
- **FR-A2**: Set question order and active/inactive status
- **FR-A3**: Preview kiosk view before publishing changes
- **FR-A4**: User management (create/deactivate staff accounts)
- **FR-A5**: Download full dataset as anonymised CSV

---

## 5. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | API response time (p95) | < 300 ms |
| NFR-2 | Uptime (excluding planned maintenance) | 99.5% |
| NFR-3 | Tablet page load (3G connection) | < 3 seconds |
| NFR-4 | WCAG accessibility level | 2.1 AA |
| NFR-5 | GDPR compliance | Full — no PII stored |
| NFR-6 | Finnish public sector accessibility act | saavutettavuusseloste ready |
| NFR-7 | Data retention | 3 years, then auto-purge |
| NFR-8 | Backup frequency | Daily, 30-day retention |

---

## 6. Out of scope (v1)

- Integration with Soite's EMR (Effica/Apotti)
- SMS/email notifications to patients
- Multi-language support beyond Finnish/English
- AI sentiment analysis (backlog item)
- Native iOS/Android app (PWA is sufficient)

---

## 7. Milestones

| Week | Deliverable |
|------|-------------|
| 1 | Repo scaffold, Docker dev environment, DB schema, migrations |
| 2 | Feedback submission API + kiosk frontend (questions + emoji scale) |
| 3 | Staff dashboard + charts |
| 4 | Admin panel + question CRUD |
| 5 | Offline PWA, auto-reset, accessibility audit |
| 6 | Security hardening, penetration test checklist, staging deploy |
| 7 | UAT with Soite team, bug fixes |
| 8 | Production deploy on HealthLab tablets, handover docs |

---

## 8. Open questions

- [ ] Will Soite provide HTTPS domain + server, or deploy on Centria infra?
- [ ] Exact question list from Minna LillKåla (awaited as of 14.4.2026)
- [ ] How many tablets will be deployed initially? (affects PWA sync strategy)
- [ ] Is there a requirement for Finnish-language admin UI or is English acceptable for staff?
