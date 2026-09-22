# NCD Patient Safety Platform

## PostgreSQL Database Design

### Work Package 10 — Database Design v0.1

**Status:** Draft / Working Database Specification
**Architecture:** Modular Django Monolith
**Database:** PostgreSQL 18.x
**ORM:** Django ORM
**Identifier Strategy:** BIGINT internal keys + UUID public identifiers + external identifier provenance
**Date:** September 2026

---

# 1. Purpose

This document defines the initial relational database architecture for the NCD Patient Safety Platform.

It translates the approved:

* project charter;
* product requirements;
* patient and caregiver journeys;
* clinical governance;
* funding governance;
* data governance;
* security architecture;
* national alignment principles;
* system architecture; and
* ADR-001 — Identifier Strategy

into a concrete PostgreSQL data model.

This document is a **database design specification**.

It is not yet the Django model implementation.

The implementation will follow only after this design has been reviewed and approved.

---

# 2. Database Objectives

The database must support:

1. patient identity;
2. caregiver delegation;
3. organizations and healthcare facilities;
4. healthcare professionals;
5. care-support cases;
6. clinical verification;
7. patient-safety workflows;
8. funding programmes;
9. funding applications;
10. funding decisions;
11. financial controls;
12. payment records;
13. service evidence;
14. reconciliation;
15. documents;
16. notifications;
17. audit;
18. governance;
19. external integrations;
20. reporting.

The database must also preserve:

* accountability;
* provenance;
* historical state;
* authorization boundaries;
* financial integrity;
* clinical separation;
* privacy;
* interoperability.

---

# 3. Core Database Principle

The database must represent **real-world entities and relationships**, not merely screens.

For example:

```text
Patient
   │
   ├── Caregiver Relationship
   │
   ├── Care-Support Case
   │       │
   │       ├── Clinical Need
   │       ├── Clinical Verification
   │       ├── Funding Application
   │       ├── Safety Event
   │       ├── Service Event
   │       └── Follow-Up
   │
   └── External Identifiers
```

A user interface may change.

The underlying domain relationships should remain stable.

---

# 4. Identifier Strategy

The database follows **ADR-001 — Identifier Strategy**.

The strategy is:

```text
INTERNAL DATABASE
BIGINT primary keys / foreign keys

        +

PUBLIC / API
UUID public identifiers

        +

EXTERNAL SYSTEMS
System + Value + Type + Provenance
```

---

# 5. Internal Primary Keys

Internal relational tables will normally use:

```text
BIGINT
```

for primary keys.

Reasons:

* compact storage;
* efficient indexes;
* efficient foreign keys;
* good PostgreSQL performance;
* simple Django ORM integration;
* appropriate for internal relational identity.

The database primary key is an implementation identifier.

It should not automatically become the identifier exposed to patients or external systems.

---

# 6. Public Identifiers

Domain objects exposed through APIs may have:

```text
public_id UUID UNIQUE NOT NULL
```

Example:

```text
Patient
-------------------------
id          BIGINT
public_id   UUID
```

The internal:

```text
id
```

is used for relational storage.

The public:

```text
public_id
```

is used where an opaque external/API identifier is required.

UUID4 is the initial implementation option because native Python support is currently available in the project environment.

A future UUID7 decision may be made separately if operational requirements justify it.

---

# 7. External Identifiers

External identifiers must not be stored by replacing the internal primary key.

Instead, external identity should be represented separately.

Conceptually:

```text
ExternalIdentifier
├── system
├── value
├── identifier_type
├── issuing_organization
├── subject
├── verification_status
├── source
├── valid_from
└── valid_to
```

Example:

```text
System:
External Registry

Value:
EXT-123456

Type:
PATIENT_REFERENCE

Source:
Authorized External System
```

This allows the same platform entity to have identifiers from multiple authorized systems.

---

# 8. Identifier Security Principle

A UUID is not an authorization mechanism.

Even when an API uses:

```text
/patients/<uuid>/
```

the backend must still verify:

```text
Who is requesting this?
        ↓
Are they authenticated?
        ↓
Are they authorized?
        ↓
Are they allowed to access this patient?
        ↓
Are they allowed to perform this action?
```

Object-level authorization remains mandatory.

---

# 9. Domain Boundaries

The database is organized conceptually into the following domains:

```text
IDENTITY
   ↓
ORGANIZATION
   ↓
PATIENT
   ↓
CASE
   ↓
CLINICAL
   ↓
SAFETY
   ↓
FUNDING
   ↓
PAYMENT
   ↓
SERVICE
   ↓
RECONCILIATION
   ↓
AUDIT / GOVERNANCE
```

Supporting domains:

```text
DOCUMENTS
NOTIFICATIONS
INTEGRATIONS
REPORTING
```

These are logical boundaries.

They do not necessarily require separate PostgreSQL databases or schemas.

---

# 10. System-of-Record Principle

PostgreSQL is the transactional system of record.

Redis must not become the permanent source of truth.

Celery task state must not become the business record.

External systems must not overwrite internal records without controlled integration logic.

For example:

```text
PostgreSQL
   ↓
Authoritative platform record

Redis
   ↓
Temporary/cache/coordination state

Celery
   ↓
Asynchronous processing

Object Storage
   ↓
Document binaries
```

---

# 11. Primary Domain Entities

The initial database design contains these major entities.

### Identity

```text
User
Role
Permission
OrganizationMembership
IdentityVerification
```

### Organization

```text
Organization
Facility
HealthcareProfessional
ProfessionalFacilityMembership
ProviderVerification
```

### Patient

```text
Patient
PatientContact
CaregiverRelationship
ExternalIdentifier
```

### Case

```text
CareSupportCase
CaseAssignment
CaseEvent
```

### Clinical

```text
ClinicalNeed
ClinicalVerification
ClinicalEvidence
CarePlan
MedicationRecord
Referral
Investigation
FollowUp
```

### Safety

```text
SafetyEvent
SafetyReport
SafetyTriage
SafetyInvestigation
CorrectiveAction
```

### Funding

```text
FundingSource
FundingProgramme
ProgrammeRule
FundingApplication
FundingReview
FundingDecision
AssistanceAuthorization
```

### Payment

```text
PaymentInstruction
Payment
PaymentAdjustment
ServiceEvidence
Reconciliation
```

### Documents

```text
Document
DocumentVersion
DocumentAccess
```

### Communication

```text
Notification
NotificationDelivery
```

### Governance

```text
ConsentAuthorization
PolicyVersion
ConfigurationVersion
AuditEvent
SecurityEvent
IntegrationEvent
```

---



# 12. Identity Database Foundation

The platform must distinguish authentication identity from domain identity.

## 12.1 Existing Django User Model

The platform already has a custom Django authentication model:

```python
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass
```

It is configured as:

```text
AUTH_USER_MODEL = 'identity.User'
```

The corresponding PostgreSQL table is:

```text
identity_user
```

The table has been directly verified in PostgreSQL.

---

## 12.2 Current User Primary Key

The existing `identity_user.id` is:

```text
BIGINT
```

and is PostgreSQL identity-generated.

This is consistent with ADR-001:

```text
Internal relational identifiers
        ↓
BIGINT
```

The existing user primary key will remain unchanged unless a future approved architecture decision requires otherwise.

---

## 12.3 Current User Constraints

The verified database constraints include:

```text
PRIMARY KEY
    identity_user.id

UNIQUE
    identity_user.username

NOT NULL
    id
    username
    password
    first_name
    last_name
    email
    is_superuser
    is_staff
    is_active
    date_joined
```

`last_login` is nullable.

These constraints are provided by the Django authentication foundation.

---

## 12.4 Authentication Identity vs Domain Identity

The `User` entity represents an authenticated platform account.

It does not automatically represent:

* a patient;
* a caregiver;
* a healthcare professional;
* a funding officer;
* a finance officer;
* an auditor;
* an organization;
* a facility.

These are separate domain relationships.

Conceptually:

```text
                         USER
                          │
                 Authentication Account
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
       PATIENT        CAREGIVER         STAFF ACTOR
                                          │
                                          ▼
                                   ORGANIZATION
```

---

## 12.5 Patient Identity

Patient identity will be represented by a dedicated `Patient` entity.

The system must not assume:

```text
User = Patient
```

Instead, an authenticated user may have an explicitly defined relationship with a patient profile.

This supports:

* patients using their own accounts;
* authorized caregivers;
* assisted access;
* staff-managed cases;
* future controlled workflows for patients who cannot directly use the platform.

---

## 12.6 Staff Identity

A staff member remains an authenticated `User`.

Their operational authority should be represented through separate relationships such as:

```text
User
  │
  └── OrganizationMembership
          │
          ├── Organization
          ├── Role
          ├── Scope
          └── Status
```

This prevents the `User` table from becoming a container for organization-specific responsibilities.

---

## 12.7 Authorization Principle

The platform should reuse Django's built-in authentication and permission framework where appropriate rather than unnecessarily duplicating its functionality.

However, authentication alone is insufficient for this platform.

Additional authorization context may include:

```text
Role
Organization Membership
Case Assignment
Facility Scope
Object-Level Authorization
Workflow State
Purpose
Consent / Legal Authority
```

Therefore:

```text
Authentication
        ≠
Authorization
        ≠
Patient Identity
        ≠
Professional Identity
```

---

## 12.8 Public User Identifiers

A public UUID will not be added to the `User` model merely because the platform uses UUIDs for public domain resources.

A public user identifier will only be introduced if an approved API/domain requirement requires users themselves to be exposed as public resources.

Patient-facing domain resources should use their own public identifiers where required.

---

## 12.9 Implementation Rule

The current `identity.User` model is the authentication foundation.

Additional identity concepts should normally be represented as separate entities and relationships.

The `User` model should not be expanded simply to accommodate future domain concepts.

This preserves:

* separation of concerns;
* authorization clarity;
* database normalization;
* security reviewability;
* future interoperability.



# 13. Relationship Philosophy

Relationships must represent actual authority and ownership.

For example:

```text
Patient
   │
   └── CareSupportCase
```

means:

> This case belongs to this patient.

Whereas:

```text
User
   │
   └── CaseAssignment
```

means:

> This user has been assigned responsibility for this case.

These are different relationships and should not be collapsed.

---

# 14. Historical Integrity

Important historical records should not be silently overwritten.

Examples:

```text
FundingDecision
Payment
PaymentAdjustment
AuditEvent
ClinicalVerification
SafetyInvestigation
```

If a correction is required, the system should preserve the original record where appropriate and create a new event, version or adjustment.

---

# 15. Deletion Principle

The platform will not use blanket deletion rules.

Different data categories require different treatment.

For example:

```text
Temporary operational data
    → may be deleted

Patient records
    → retention policy

Financial records
    → controlled retention

Clinical records
    → clinical/legal retention rules

Audit records
    → protected retention

Documents
    → retention policy
```

Deletion and retention requirements will be governed by the approved Data Governance and Privacy specification.

---

# 16. Foreign-Key Principle

Foreign keys should normally use:

```text
BIGINT
```

to match internal primary keys.

Example:

```text
care_support_case.patient_id
        ↓
patient.id
```

Public UUIDs should not normally be used as the relational foreign-key mechanism unless a later architecture decision explicitly requires it.

---

# 17. Timestamp Principle

Important entities should normally contain:

```text
created_at
updated_at
```

where appropriate.

Workflow events should additionally record the event timestamp.

Financial and clinical events must preserve the relevant business timestamp rather than relying only on database insertion time.

Example:

```text
created_at
occurred_at
approved_at
completed_at
```

These represent different concepts.

---

# 18. Time Zone Principle

All stored timestamps should be timezone-aware.

The application should operate using UTC internally.

User interfaces may convert timestamps to the user's appropriate local timezone.

This avoids ambiguity when:

* patients move;
* providers operate across locations;
* external systems operate in different time zones;
* audits cross jurisdictions.

---

# 19. Money Principle

Financial amounts should not use floating-point database fields.

Use an exact monetary representation.

Initial design:

```text
NUMERIC(19,2)
```

with:

```text
currency_code
```

stored separately.

Example:

```text
amount = 150000.00
currency_code = NGN
```

The final precision and currency rules remain subject to financial-domain review.

---

# 20. Status Principle

Statuses should represent meaningful business states.

Avoid using vague values such as:

```text
ACTIVE
INACTIVE
```

for every domain.

Instead:

```text
FundingApplication:
SUBMITTED
UNDER_REVIEW
APPROVED
DECLINED
...
```

Status transitions should be controlled by application services.

Where the history matters, a separate transition/event record should be maintained.

---

# 21. Audit Principle

Important database mutations must produce meaningful audit events.

An audit record should be capable of answering:

```text
WHO?
WHAT?
WHEN?
ON WHICH OBJECT?
WHAT CHANGED?
WHY?
UNDER WHICH AUTHORITY?
```

The audit system should not depend solely on database triggers or web-server logs.

Business-level audit events should be generated by the application layer.

---

# 22. Privacy Principle

The database must support data minimization.

Do not create fields merely because they might be useful someday.

Every sensitive field should have:

```text
Purpose
Access Rule
Retention Rule
```

Health and financial information should receive stronger access controls than ordinary operational metadata.

---

# 23. Database Design Rule

We will design the database in this order:

```text
1. Identity
2. Organization
3. Facility
4. Healthcare Professional
5. Patient
6. Caregiver
7. Case
8. Clinical
9. Safety
10. Funding
11. Payment
12. Service Evidence
13. Reconciliation
14. Documents
15. Notifications
16. Audit
17. Governance
18. Integration
19. Reporting
```

This ordering reduces circular design errors.

---

# 24. Database Implementation Boundary

This document defines the **logical and relational design**.

The following will be produced later:

```text
Database Design
      ↓
Django Models
      ↓
Migrations
      ↓
Constraints
      ↓
Indexes
      ↓
Tests
```

No production database schema should be considered final until the corresponding governance requirements and migrations have been reviewed.

---

# 25. Current Status

```text
Database architecture        DEFINED
Identifier strategy          DEFINED
Domain boundaries            DEFINED
Primary-key strategy         DEFINED
Public-ID strategy           DEFINED
External-ID strategy         DEFINED
Timestamp strategy           DEFINED
Money representation         PROVISIONAL
Retention/deletion            GOVERNED ELSEWHERE
Detailed table definitions    NEXT SECTION
Django implementation         NOT STARTED
```

---
