# GDPR.md — Data Protection & Privacy

## 1. Legal basis

This system processes feedback data on behalf of **Soite** (Keski-Pohjanmaan hyvinvointialue), a Finnish public sector wellbeing services county. Processing is based on:

- **Article 6(1)(e)** — processing necessary for a task in the public interest
- **No special-category data is collected** — feedback is anonymous; no health data is linked to identifiable persons

If a patient voluntarily includes identifying information in a free-text field, it is:
1. Encrypted at rest (pgcrypto)
2. Not linked to any patient record
3. Not shared with any third party
4. Purged after 3 years

---

## 2. Data minimisation

| What we do NOT collect | Why |
|------------------------|-----|
| Patient name | Not needed for aggregate statistics |
| Date of birth | Not needed |
| Treatment details | Not needed |
| IP address of patient | Rate limiting uses device token only |
| Browser fingerprint | Not implemented |
| Cookies on kiosk | No cookies on anonymous kiosk view |

---

## 3. Data subject rights

Because submissions are anonymous, **data subject access and erasure requests cannot be fulfilled** for individual submissions — there is no way to identify which submission belongs to which person. This design choice must be communicated clearly in the privacy notice.

For staff users (identifiable):
- **Access**: export personal data on request
- **Rectification**: email/name update via admin
- **Erasure**: deactivation + anonymisation after 1 year (see DATABASE.md)
- **Portability**: CSV export of own audit log entries

---

## 4. Privacy notice (patient-facing, displayed on kiosk before survey)

> **Tietosuoja / Privacy**
>
> Tämä kysely on täysin anonyymi. Emme kerää nimeäsi, henkilötunnustasi tai muita tunnistetietoja. Antamiasi vastauksia käytetään vain Soiten kotikuntoutuksen palvelun kehittämiseen.
>
> *This survey is completely anonymous. We do not collect your name, personal ID, or any other identifying information. Your responses are used solely to improve Soite's home rehabilitation service.*

---

## 5. Data retention schedule

| Data | Retention | Basis |
|------|-----------|-------|
| Feedback submissions & answers | 3 years | Operational need |
| Free-text (encrypted) | 3 years | Same |
| Staff user accounts | 1 year after deactivation | Employment records |
| Audit log | 5 years | Finnish public sector record-keeping |
| Access/error logs (Nginx) | 90 days | Security monitoring |
| Backup files | 30 days | Recovery |

Automated purge: a scheduled job (`purge_old_data.py`) runs monthly and deletes records past retention period.

---

## 6. Data processing agreement

A **Data Processing Agreement (DPA)** must be signed between:
- **Controller**: Soite (Keski-Pohjanmaan hyvinvointialue)
- **Processor**: Centria University of Applied Sciences (during development and pilot)
- **Sub-processor**: Hosting provider (if cloud deployment)

This is a prerequisite for going live. Template DPA available from the Finnish Data Protection Ombudsman (tietosuojavaltuutettu.fi).

---

## 7. Security measures (Article 32)

- Encryption in transit: TLS 1.2 minimum
- Encryption at rest: pgcrypto for free-text fields; database volume encryption recommended at OS level
- Access control: role-based; principle of least privilege
- Audit trail: all admin actions logged
- Incident response: 72-hour notification window to DPA (GDPR Article 33)

---

## 8. Breach notification procedure

1. Detect incident (monitoring alert or manual discovery)
2. Within **24 hours**: notify Soite DPO and Centria supervisor
3. Within **72 hours**: Soite DPO notifies Finnish Data Protection Ombudsman if risk to individuals
4. Document: what happened, what data, how many people affected, mitigations taken
5. If high risk to individuals: notify affected persons without undue delay

Contact: Finnish Data Protection Ombudsman — tietosuojavaltuutettu@om.fi
