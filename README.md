# 🏥 NCD Patient Safety Platform

> **National Healthcare Aid, Care Coordination & Financial Governance Network**  
> A sovereign, standards-based digital health platform designed to safeguard people living with chronic noncommunicable diseases (NCDs) across Nigeria. Built on Python 3.12, Django 5.2, PostgreSQL 18, Redis 8, and Celery 5.6, aligned with the **Nigeria Digital Health Architecture (NDHA)**.

---

## 📋 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture & Engineering Streams](#-system-architecture--engineering-streams)
  - [Engineer A: Clinical, Patient & Safety Stream](#1-engineer-a-clinical-patient--safety-stream)
  - [Engineer B: Funding, Payments & Financial Governance Stream](#2-engineer-b-funding-payments--financial-governance-stream)
- [Governance & Integrity Pillars](#-governance--integrity-pillars)
- [Live Portals & User Experiences](#-live-portals--user-experiences)
- [Complete REST API Catalog (Swagger/OpenAPI)](#-complete-rest-api-catalog)
- [Getting Started & Local Setup](#-getting-started--local-setup)
  - [Option 1: Docker Compose (Production Environment)](#option-1-docker-compose-recommended)
  - [Option 2: Local Python Environment](#option-2-local-python-environment)
- [Hydrating Demo Data (`seed_demo_data`)](#-hydrating-demo-data)
- [Running Automated Tests](#-running-automated-tests)
- [National Alignment (NDHA & NDPA)](#-national-alignment-ndha--ndpa)

---

## 🌟 Executive Summary

Noncommunicable diseases (cardiovascular disease, end-stage renal disease, cancer, and diabetes) place catastrophic financial and medical burdens on Nigerian families. The **NCD Patient Safety Platform** bridges clinical science with transparent financial governance. It ensures that humanitarian medical subsidies and government intervention funds reach accredited healthcare providers directly, with zero diversion, backed by verifiable clinical evidence and multi-tier institutional accountability.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 END-TO-END PATIENT AID LIFECYCLE                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
  [1. Patient Intake]       [2. Clinical Verification]      [3. Four-Eyes Governance]      [4. Direct Settlement]
  NIN/NHIA Provenance   ──► Accredited Doctor Certifies ──► Committee Review & Approval ──► Payout Directly to
  & Caregiver Authority      Diagnosis with SHA-256 Seal     Assistance Envelope Issued      Hospital via NIBSS
```

---

## 🏗️ System Architecture & Engineering Streams

The platform is architected as a modular Django monolith enforcing strict domain boundaries and the **ADR-001 Identifier Strategy** (`BIGINT` internal relational keys + `UUID` opaque public API identifiers + external system provenance).

```
NCD-Patient-Safety-Platform/
├── src/
│   ├── apps/
│   │   ├── identity/          # Custom User model, auth, and seed management
│   │   ├── organizations/     # Accredited Hospitals, Facilities & Licensed Professionals
│   │   ├── patients/          # Demographics, Caregiver delegation, NIN/NHIA provenance
│   │   ├── clinical_need/     # Diagnoses, ICD-10 mapping, SHA-256 evidence, Clinician Portal
│   │   ├── cases/             # Care coordination backbone (Open → Verified → Active)
│   │   ├── safety/            # Clinical adverse event and safety incident reporting
│   │   ├── funding/           # Funding sources, programmes, reviews, decisions, authorisations
│   │   └── payments/          # Payment instructions, NIBSS settlement, service evidence, reconciliation
│   ├── config/                # Django settings, Celery app, WSGI/ASGI, URLs
│   └── templates/             # Responsive Tailwind CSS portals & national aid landing pages
├── docs/                      # Architectural decision records (ADR) & NDHA integration readiness
├── Dockerfile                 # Multi-stage secure runner (non-root ncduser)
└── docker-compose.yml         # Full orchestration: Web + PostgreSQL 18 + Redis 8 + Celery
```

---

### 1. Engineer A: Clinical, Patient & Safety Stream
*Focus: Patient identity, clinical governance, case coordination, and safety.*

- **`apps.patients`**:
  - Demographics, genotype, blood group, and multi-channel contact verification.
  - **Delegated Caregiver Authority Matrix**: Granular legal permissions (`can_view_records`, `can_manage_care`, `can_apply_funding`) protected against cascade deletions.
  - **External Identifier Provenance**: Provenance tracking for National Identity Numbers (NIN), NHIA insurance numbers, and hospital EMR references.
- **`apps.clinical_need`**:
  - Diagnosis tracking mapped to standard ICD-10 codes (e.g., `C50.9` for breast cancer, `N18.6` for end-stage renal disease).
  - **Clinical Verification**: Legal audit trail ensuring only accredited doctors at verified facilities can certify medical conditions.
  - **Cryptographic Evidence Sealing**: Attachment of pathology, radiology, and prescription records sealed with SHA-256 checksums.
- **`apps.cases`**:
  - Central care coordination lifecycle state machine:
    $$\text{OPEN} \longrightarrow \text{CLINICAL\_REVIEW} \longrightarrow \text{FUNDING\_ELIGIBLE} \longrightarrow \text{ASSISTANCE\_ACTIVE}$$
  - Operational staff assignments (Case Officer, Clinical Lead, Caregiver Liaison, Auditor).
- **`apps.safety`**:
  - Patient safety incident and adverse event reporting with severity triage (`NEAR_MISS` to `CRITICAL`), immediate remediation recording, and case linking.
- **`apps.organizations`**:
  - Directory of accredited healthcare providers, teaching hospitals, diagnostic centres, and verified healthcare professionals.

---

### 2. Engineer B: Funding, Payments & Financial Governance Stream
*Focus: Donor transparency, institutional funds, multi-party approvals, disbursements, and audits.*

- **`apps.funding`**:
  - **Institutional Funding Pools**: Management of government grants, corporate CSR, and philanthropic foundations (`FundingSource` & `FundingProgramme`) with real-time budget and disbursement tracking.
  - **Pre-Funding Eligibility Gate**: Programmatically prevents any funding application from being submitted unless the case status is `FUNDING_ELIGIBLE` and backed by a verified clinical diagnosis.
  - **Four-Eyes Committee Governance**: Formal assessment (`FundingReview`) and grant decisions (`FundingDecision`).
  - **Assistance Authorization Envelopes**: Formal financial ceiling allocated per patient case with automatic remaining balance monitoring.
- **`apps.payments`**:
  - **Payment Instructions**: Payment mandates generated against active authorizations with balance verification and separation-of-duties enforcement.
  - **Direct-to-Provider Settlement**: Banking execution records (via NIBSS Instant Payment or Direct Bank Transfer) capturing gateway session IDs and transaction responses.
  - **Service Evidence & Clawbacks**: Itemized medical invoices verified with SHA-256 seals, plus immutable ledger adjustments (`PaymentAdjustment`).
  - **Periodic Financial Reconciliation**: Automated comparison of authorized payment mandates against actual bank settlement responses, flagging any balance discrepancies.
- **Asynchronous Task Architecture**:
  - Celery 5.6 integrated with Redis 8 task broker for scheduled reconciliation audits, batch settlement executions, and notification alerts.

---

## 🔒 Governance & Integrity Pillars

| Governance Rule | Architectural Enforcement |
| :--- | :--- |
| **Separation of Clinical & Financial Authority** | Clinicians certify medical diagnoses; they cannot authorize financial disbursements. |
| **Pre-Funding Eligibility Gate** | `FundingApplication.clean()` rejects submissions unless the case has a verified diagnosis (`status == FUNDING_ELIGIBLE`). |
| **Four-Eyes Principle (Decision Maker)** | `FundingDecision.clean()` strictly prevents the user who submitted the application from acting as the decision maker. |
| **Payment Authorization Separation** | `PaymentInstruction.clean()` prevents the officer who authorized the instruction from being the user who approved the funding decision. |
| **Settlement Execution Separation** | `Payment.clean()` ensures the officer executing the bank transaction is distinct from the instruction authorizer. |
| **Balance Ceiling Enforcement** | Payment instruction amounts cannot exceed the authorization's `remaining_balance`. |
| **Exact Monetary Representation** | All currency balances use `Decimal(19, 2)` to eliminate floating-point rounding errors. |
| **Zero Aid Diversion** | Subsidies are disbursed directly to accredited hospital/pharmacy NUBAN accounts. |

---

## 🖥️ Live Portals & User Experiences

The platform provides dedicated, role-specific interfaces:

1. **National Aid Landing Page (`/`)**:
   - Public institutional aid portal displaying live platform telemetry (enrolled patients, accredited hospital network, active cases, total subsidy pool).
   - Showcases active disease envelopes (Renal, Oncology, Diabetes, Cardiovascular) and donor trust pillars.
2. **Hospital & Clinician Portal (`/portal/clinician/`)**:
   - Dedicated workspace for licensed medical practitioners (MDCN/NMCN verified).
   - Review pending cases, certify clinical diagnoses, attach SHA-256 sealed lab evidence, onboard patients, and log adverse safety events.
3. **Funding & Financial Governance Portal (`/portal/funding/`)**:
   - Dedicated interface for Case Officers, Reviewers, Committee Approvers, and Treasury Officers.
   - Intake applications for verified cases, record committee recommendations, execute Four-Eyes approvals, issue `AssistanceAuthorization` envelopes, generate payment instructions, execute direct settlements, and run 30-day banking reconciliation audits.
4. **Patient Eligibility Self-Assessment (`/eligibility-check/`)**:
   - Patient- and caregiver-facing questionnaire matching individuals with active national subsidies.
5. **Interactive Swagger & ReDoc API Documentation (`/api/docs/` and `/api/redoc/`)**:
   - Live interactive OpenAPI 3.0 catalog documenting all clinical, patient, safety, funding, and payment endpoints.
6. **System Administration Desk (`/admin/`)**:
   - Internal administrative control center with filtered views, search, and audit trails.

---

## 📡 Complete REST API Catalog

All endpoints are versioned under `/api/v1/` and documented in Swagger at `/api/docs/`:

### Clinical & Patient Stream (Engineer A)
- `GET /api/v1/patients/` — List & search patient demographic records
- `POST /api/v1/patients/` — Onboard new patient with NIN/NHIA provenance
- `GET /api/v1/caregivers/` — Delegated caregiver relationship matrix
- `GET /api/v1/clinical-needs/` — Clinical diagnoses and ICD-10 codes
- `GET /api/v1/clinical-verifications/` — Licensed clinician verification records
- `GET /api/v1/clinical-evidence/` — Cryptographically sealed medical records
- `GET /api/v1/cases/` — Care support cases and coordination lifecycles
- `GET /api/v1/safety-events/` — Clinical adverse safety incident reporting
- `GET /api/v1/facilities/` — Accredited hospitals, clinics, and dialysis centres
- `GET /api/v1/healthcare-professionals/` — Licensed doctor and nurse registry

### Funding & Financial Stream (Engineer B)
- `GET /api/v1/funding/sources/` — Institutional donor and government funding pools
- `GET /api/v1/funding/programmes/` — Disease assistance schemes and budget limits
- `POST /api/v1/funding/applications/` — Submit assistance request for verified case
- `GET /api/v1/funding/authorizations/` — Active patient financial envelopes and balances
- `POST /api/v1/payments/instructions/` — Authorize payment instruction to hospital
- `POST /api/v1/payments/records/` — Record direct banking settlement execution
- `GET /api/v1/payments/evidence/` — Itemized service invoices and dispensing logs
- `GET /api/v1/payments/reconciliations/` — Banking ledger reconciliation audit logs

---

## 🚀 Getting Started & Local Setup

### Option 1: Docker Compose (Recommended)

Spins up the full stack including PostgreSQL 18, Redis 8, Django (Gunicorn), and Celery:

```bash
# 1. Clone repository
git clone https://github.com/antenyijoseph20-glitch/NCD-Patient-Safety-Platform.git
cd NCD-Patient-Safety-Platform

# 2. Configure environment
cp .env.example .env

# 3. Build and launch containers
docker compose up -d --build

# 4. Populate realistic demo dataset
docker compose exec web python manage.py seed_demo_data
```

The platform will be live at:
- **Web Portal:** `http://localhost:8000`
- **Clinician Portal:** `http://localhost:8000/portal/clinician/`
- **Funding & Governance Portal:** `http://localhost:8000/portal/funding/`
- **Swagger API Docs:** `http://localhost:8000/api/docs/`
- **Health Check:** `http://localhost:8000/healthz/`

---

### Option 2: Local Python Environment

For local development with an SQLite database:

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure local environment
cat << 'EOF' > .env
DJANGO_SECRET_KEY=local-dev-secret-key-2026
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
REDIS_URL=redis://localhost:6379/0
EOF

# 4. Run migrations
python src/manage.py migrate

# 5. Hydrate demo dataset
python src/manage.py seed_demo_data

# 6. Start development server
python src/manage.py runserver 0.0.0.0:8000
```

---

## 🧪 Hydrating Demo Data

The platform includes a management command that provisions an authentic Nigerian clinical and funding ecosystem:

```bash
python src/manage.py seed_demo_data
```

This creates:
- **Accredited Providers**: National Hospital Abuja (Oncology Complex), Lagos University Teaching Hospital (Renal & Dialysis Centre).
- **Verified Clinicians**: Dr. Fatima Audu (Oncologist, `MDCN-102938`), Dr. Chidi Eze (Nephrologist, `MDCN-204958`).
- **Real Patients**: Indigent patients with confirmed diagnoses (Stage IIIb Breast Carcinoma, End-Stage Renal Disease).
- **Active Funds**: FMOH National NCD Fund (NGN 150M), Dangote Foundation Health CSR (NGN 75M).
- **Active Programmes**: Renal Dialysis Lifeline, Oncology Diagnostics & Chemo Subsidy.
- **Settlement Records**: Approved decisions, payment instructions to LUTH, and completed NIBSS settlements.

---

## 🔬 Running Automated Tests

Run the full automated test suite:

```bash
python src/manage.py test apps.cases apps.clinical_need apps.funding apps.identity apps.organizations apps.patients apps.payments apps.safety
```

To run tests with verbose output:

```bash
python src/manage.py test apps.funding apps.payments -v 2
```

---

## 🏛️ National Alignment (NDHA & NDPA)

- **Nigeria Digital Health Architecture (NDHA)**: The platform connects to authoritative national registries rather than duplicating them. It supports external identifier links for NIN (National Identity Management Commission) and NHIA (National Health Insurance Authority).
- **Nigeria Data Protection Act (NDPA)**: Enforces privacy-by-design, cryptographic SHA-256 evidence sealing, contextual access control, and least-privilege principles.
- **NHTDAO Coordination**: Structured for compatibility with emerging national health information exchange (HIE) and digital health building blocks.

---

## 👥 Contributors & Stream Leads

- **Clinical, Patient & Safety Stream (Engineer A)**: Adanu Oche Gabriel (`oche8004@gmail.com`) — *B.N.Sc., Registered Nurse (RN), AI-Native Full Stack Engineer*
- **Funding, Payments & Financial Governance Stream (Engineer B)**: Antenyi Joseph Ochohepo (`antenyijoseph20@gmail.com`) — *Software Engineer & DevOps*
