# NCD Patient Safety Platform
## NDHA Integration Readiness
### Version 0.1 — Assurance Working Document

**Status:** Architecture Assurance
**Date:** September 2026
**Classification:** National Alignment / Integration Readiness

---

# 1. Purpose

This document records the current readiness position of the NCD Patient Safety Platform for eventual integration with Nigeria's national digital-health ecosystem.

It exists to prevent the project from making unsupported claims such as:

- "NDHA certified";
- "government approved";
- "nationally integrated";
- "connected to the national health registry";
- "compliant with all Nigerian health-information standards."

None of those statements should be made unless the relevant authority has formally confirmed them.

The purpose of this document is therefore to distinguish:

```text
WHAT IS VERIFIED
        ↓
WHAT WE HAVE DESIGNED
        ↓
WHAT REMAINS OPEN
        ↓
WHAT MUST BE COMPLETED
        ↓
WHAT REQUIRES EXTERNAL AUTHORITY
```

---

# 2. Current Status

## Overall Position

**National alignment:** VERIFIED DIRECTION

**Architecture alignment:** IN PROGRESS

**Technical integration:** NOT STARTED

**National validation:** NOT STARTED

**Certification:** NOT STARTED

**Production integration:** NOT AUTHORIZED

The platform is being designed to align with Nigeria's approved digital-health architecture and interoperability direction.

It is **not currently represented as a nationally certified or production-integrated application**.

---

# 3. Critical Principle

The project follows:

> **CONNECT TO AUTHORITATIVE NATIONAL SERVICES WHERE AVAILABLE; DO NOT DUPLICATE THEM.**

The platform should maintain only the local information required to perform its own legitimate operational functions.

This means the platform should not attempt to become:

- Nigeria's national patient registry;
- Nigeria's national facility registry;
- Nigeria's national healthcare-worker registry;
- Nigeria's national shared health record;
- Nigeria's national health-information exchange;
- Nigeria's national claims exchange.

Instead, the platform should be capable of integrating with authoritative national infrastructure when the applicable technical, legal, security and certification requirements are satisfied.

---

# 4. Verified NDHA Direction

The Nigeria Digital Health Architecture describes an interoperable digital-health ecosystem built around shared digital-health building blocks.

The architecture identifies national infrastructure including areas such as:

```text
Health Client Registry
Health Facility Registry
Healthcare Worker Registry
Health Information Exchange
Health Claims Exchange
Shared Health Record
Terminology Services
Drug-related services
```

The platform therefore needs to be designed as an ecosystem participant rather than an isolated national replacement system.

---

# 5. Public and Private Application Integration

The NDHA documentation states that applications from both public and private actors can integrate with the national building blocks.

The architecture also states that the responsible national digital-health organization will define the integration process, validate integration and provide a certificate of compliance.

The NDHA documentation further states that only certified applications will be permitted to connect to the building blocks in production.

### Platform implication

We must distinguish:

```text
Application can technically integrate
```

from:

```text
Application has been nationally validated
```

and:

```text
Application is certified for production connection
```

These are not the same condition.

---

# 6. Current National Authority Position

The Federal Ministry of Health and Social Welfare announced in September 2026 the establishment of the National Health Technology and Data Analytics Office (NHTDAO) as a coordination mechanism for digital-health transformation.

The Ministry identified:

- interoperability;
- cybersecurity;
- data protection;
- ethical AI;
- data governance;
- patient confidentiality

as important areas of national digital-health coordination.

However, the exact current operational application/certification pathway for this project must be verified with the responsible national authority before any production integration claim is made.

### Status

**OPEN / VERIFY CURRENT PROCEDURE**

We must not assume that an older organizational name, office structure or contact process remains unchanged.

---

# 7. National Health Client Registry

The platform should not create a competing national patient registry.

The local platform may maintain:

```text
Patient
```

as an operational entity.

However, where national identity services are available and integration is authorized, the platform should be capable of maintaining references to authoritative external identifiers.

Conceptually:

```text
LOCAL PATIENT
     │
     ├── Internal Platform Identifier
     │
     └── External National Identifier
              │
              ├── Identifier System
              ├── Source
              ├── Verification Status
              └── Provenance
```

The local identifier must not be presented as the national health-client identifier.

---

# 8. NIN and Health Identity

The platform must not assume that:

```text
NIN = National Health Client Identifier
```

These are different concepts unless an authoritative specification establishes otherwise.

Any future identity integration must document:

- identifier type;
- issuing authority;
- source system;
- verification method;
- permitted use;
- data-sharing purpose;
- retention requirements;
- matching rules.

---

# 9. Duplicate Patient Handling

Duplicate detection remains necessary even where a national identity service exists.

The platform should support:

```text
Potential Duplicate
        ↓
Matching
        ↓
Review
        ↓
Confirm / Reject
        ↓
Controlled Resolution
```

The system must not automatically merge patients solely because names, phone numbers or other ordinary demographic information appear similar.

High-impact identity resolution requires appropriate controls and, where necessary, human adjudication.

---

# 10. National Health Facility Registry

The platform should not become a competing national facility master list.

The local system may maintain:

```text
Organization
Facility
Facility Participation
Provider Relationship
```

but should be capable of storing the authoritative external facility identifier when available.

Conceptually:

```text
LOCAL FACILITY
      │
      ├── Internal Facility ID
      │
      ├── National Facility ID
      │
      ├── Source
      │
      └── Verification Status
```

---

# 11. Facility Identity vs Platform Participation

These concepts must remain separate.

A facility can be:

```text
Nationally Registered
```

without necessarily being:

```text
Participating in this Platform
```

Similarly:

```text
Platform Participant
```

must not automatically imply:

```text
Nationally Registered Facility
```

The system should maintain separate states for these concepts.

---

# 12. Healthcare Worker Registry

The same principle applies to healthcare professionals.

The platform may maintain a local:

```text
HealthcareProfessional
```

record for operational purposes.

Where the national healthcare-worker registry is available and integration is authorized, the platform should retain the authoritative external identifier and provenance.

The platform must not represent its own local professional identifier as a national professional identifier.

---

# 13. Registry Verification vs Authorization

This distinction is mandatory.

For example:

```text
Registry Verification
        ≠
Platform Role
```

and:

```text
National Facility Registration
        ≠
Funding Programme Participation
```

and:

```text
Healthcare Worker Registry Identity
        ≠
Permission to perform every action in this platform
```

The platform's authorization system remains responsible for determining what an authenticated user is permitted to do.

---

# 14. FHIR / Health Information Exchange

The NDHA identifies standards-based interoperability and FHIR as part of the national digital-health direction.

The platform should therefore support FHIR at the **external interoperability boundary**.

It should not force the internal PostgreSQL database to become a FHIR database.

The architecture remains:

```text
INTERNAL DOMAIN MODEL
        ↓
FHIR ADAPTER
        ↓
NIGERIAN FHIR PROFILE / IMPLEMENTATION REQUIREMENT
        ↓
AUTHORIZED HEALTH INFORMATION EXCHANGE
```

---

# 15. Internal Domain Model Remains Independent

The platform's internal model should continue to represent its own domain concepts:

```text
Patient
CareSupportCase
ClinicalNeed
ClinicalVerification
SafetyEvent
FundingApplication
FundingDecision
AssistanceAuthorization
Payment
ServiceEvidence
Reconciliation
```

These should not be replaced simply because an external exchange uses FHIR.

FHIR is an interoperability representation.

It is not automatically the correct internal persistence model.

---

# 16. Nigerian FHIR Profiles

FHIR implementation must not be treated as complete merely because the platform can produce generic FHIR resources.

Before production integration, we must identify the applicable Nigerian:

- implementation guides;
- profiles;
- extensions;
- identifier systems;
- terminology requirements;
- value sets;
- code systems;
- exchange mechanisms;
- validation requirements.

### Status

**OPEN / VERIFY CURRENT SPECIFICATIONS**

No specific profile should be invented.

---

# 17. Terminology

The architecture must eventually support appropriate terminology mappings.

Potential standards identified in the national digital-health architecture include:

- ICD-10;
- ICD-11;
- ICD-10-PCS;
- LOINC;
- national terminology services;
- applicable medicine/drug terminology.

The platform should not hard-code unsupported local codes merely to make an early prototype appear interoperable.

### Principle

```text
Authoritative terminology
        ↓
Versioned mapping
        ↓
Internal representation
        ↓
FHIR/external representation
```

---

# 18. Shared Health Record Boundary

The platform's:

```text
Care-Support Case
```

must not be confused with:

```text
National Shared Health Record
```

The Care-Support Case is a platform workflow object.

The Shared Health Record is part of the wider health-information ecosystem.

The platform should only exchange information that is:

- authorized;
- relevant;
- necessary;
- appropriately structured;
- permitted by the applicable legal and governance framework.

---

# 19. Health Claims Exchange

The national digital-health architecture also describes a Health Claims Exchange.

This may become relevant if the platform eventually integrates with:

- insurance;
- claims;
- eligibility;
- preauthorization;
- provider empanelment;
- payments;
- disputes;
- appeals.

However:

```text
Funding Assistance
        ≠
Insurance Claim
```

The platform should therefore keep its funding-support model separate from an eventual claims-exchange integration.

---

# 20. Offline and Low-Connectivity Requirements

The national architecture recognizes operational realities including:

- intermittent connectivity;
- feature phones;
- non-smartphone users;
- low digital literacy;
- assisted access;
- inclusion requirements.

These conditions are relevant to the platform's intended patient population.

### MVP direction

The initial system should provide:

```text
Responsive Web
      +
Assisted Access
      +
Graceful Failure
      +
Retry/Pending States
      +
Notification Fallback
```

A fully offline mobile workflow may be introduced later after the appropriate architecture and security requirements are established.

---

# 21. Offline Submission Boundary

The platform must distinguish:

```text
DRAFTED OFFLINE
```

from:

```text
SUBMITTED TO SERVER
```

An offline device must never display an application as officially submitted until the authoritative server has accepted it.

For example:

```text
OFFLINE DRAFT
      ↓
LOCAL VALIDATION
      ↓
CONNECTIVITY RESTORED
      ↓
SERVER SUBMISSION
      ↓
SERVER ACCEPTANCE
      ↓
SUBMITTED
```

---

# 22. Offline High-Impact Decisions

High-impact actions should remain server-controlled by default.

Examples:

- funding approval;
- payment authorization;
- privileged administrative changes;
- clinical verification;
- identity adjudication.

An offline client should not be able to manufacture an authoritative approval.

---

# 23. Future Offline Synchronization

If offline operation becomes a production requirement, the design must include:

- local draft state;
- synchronization state;
- version numbers;
- timestamps;
- conflict detection;
- duplicate submission protection;
- authorization revalidation;
- server-side acceptance;
- conflict resolution;
- audit history.

The exact offline architecture remains:

**DECISION REQUIRED**

---

# 24. Data Protection

The platform will process sensitive health and support-related information.

The Nigeria Data Protection Act 2023 and applicable GAID requirements therefore form a major compliance boundary.

The platform must not treat privacy as an optional feature.

Required areas include:

```text
Lawful Processing
Purpose Limitation
Data Minimization
Access Control
Security
Retention
Data Subject Rights
Processor Governance
Breach Response
DPIA
Cross-Border Processing Assessment
Auditability
```

---

# 25. Consent Is Not the Entire Privacy Model

The platform must distinguish:

```text
Lawful Basis
        +
Consent Where Applicable
        +
Authorization
        +
Purpose
        +
Access Control
        +
Data Minimization
```

Consent should not automatically be treated as the legal basis for every processing activity.

The exact lawful basis for each processing activity must be determined through the project's data-governance and legal review.

---

# 26. Consent / Authorization Model

The existing platform design should therefore support richer authorization concepts, potentially including:

```text
Consent
Authorization
Delegation
Representative Authority
Data-Sharing Permission
Purpose
Scope
Effective Date
Expiry
Withdrawal
Source
```

The final controlled vocabulary remains:

**DECISION REQUIRED**

---

# 27. DPIA

A Data Privacy Impact Assessment is a required project gate before production where applicable.

Given the platform's intended processing of health information, vulnerable data subjects and potentially high-impact processing, the project must complete a formal privacy assessment before production deployment.

The DPIA should identify:

- processing activities;
- data categories;
- purposes;
- lawful bases;
- data flows;
- recipients;
- risks;
- mitigations;
- retention;
- cross-border processing;
- processor relationships;
- data-subject impacts;
- residual risks;
- approval/sign-off.

### Status

**NOT STARTED**

---

# 28. Data Processor Governance

External processors must not be selected merely because their technology works.

Before production, processor due diligence should cover:

- contractual controls;
- security;
- data location;
- transfer arrangements;
- incident response;
- access control;
- relevant certifications;
- data retention/deletion;
- subcontractors;
- business continuity.

The applicable Nigerian data-protection requirements must govern the final processor assessment.

---

# 29. Security Testing

Before national production integration, the platform should complete appropriate:

```text
Application Security Testing
API Security Testing
Authentication Testing
Authorization Testing
BOLA Testing
Input Validation Testing
Rate-Limit Testing
File Upload Testing
Integration Security Testing
Dependency/Supply-Chain Review
Penetration Testing
```

High-impact financial and patient-safety workflows require dedicated security testing.

---

# 30. External Integration Security

No national or partner system should receive direct database access.

The architecture remains:

```text
EXTERNAL SYSTEM
      ↓
INTEGRATION GATEWAY
      ↓
AUTHENTICATION
      ↓
AUTHORIZATION
      ↓
VALIDATION
      ↓
TRANSFORMATION
      ↓
DOMAIN SERVICE
      ↓
AUDIT
```

---

# 31. External Exchange Audit

Every material external exchange should be capable of answering:

```text
Who?
What?
When?
Which system?
Which identifier?
For what purpose?
Under what authorization?
What was sent?
What was received?
What happened afterward?
```

Integration events must remain auditable.

---

# 32. Failure-Safe Integration

External systems can fail.

The platform must support:

```text
Timeout
Retry
Duplicate Response
Delayed Response
Malformed Response
Unavailable Partner
Partial Failure
Authentication Failure
Authorization Failure
```

A partner outage must not corrupt the patient case.

A failed payment request must not silently become a successful payment.

A duplicate external message must not automatically create duplicate financial or clinical records.

---

# 33. Production Sandbox Requirement

Before production integration:

```text
Development
      ↓
Integration Sandbox
      ↓
Conformance Testing
      ↓
Security Testing
      ↓
Validation
      ↓
Certification
      ↓
Controlled Production
```

Development credentials must never be connected directly to national production systems.

---

# 34. API Contract

The platform should maintain a machine-readable API contract.

Target:

```text
OpenAPI
```

Current platform API direction:

```text
/api/v1/
```

External integrations must use documented contracts.

The API contract should define:

- authentication;
- authorization;
- request schemas;
- response schemas;
- errors;
- versioning;
- pagination;
- rate limits;
- idempotency;
- audit/correlation identifiers.

---

# 35. National Integration Readiness Gates

The following gates are required before production integration.

| ID | Gate | Status |
|---|---|---|
| G1 | Formal integration pathway identified | OPEN |
| G2 | Responsible national authority confirmed | OPEN / VERIFY |
| G3 | NDHA technical requirements mapped | IN PROGRESS |
| G4 | National identifiers mapped | OPEN |
| G5 | Health Client Registry integration defined | OPEN |
| G6 | Facility Registry integration defined | OPEN |
| G7 | Healthcare Worker Registry integration defined | OPEN |
| G8 | FHIR/Nigerian profiles mapped | OPEN |
| G9 | Terminology mappings verified | OPEN |
| G10 | API contract completed | IN PROGRESS |
| G11 | Integration authentication designed | IN PROGRESS |
| G12 | Object-level authorization tested | DESIGNED |
| G13 | External audit logging implemented | DESIGNED |
| G14 | Data-protection assessment completed | IN PROGRESS |
| G15 | DPIA completed | NOT STARTED |
| G16 | Processor controls completed | NOT STARTED |
| G17 | Security testing completed | NOT STARTED |
| G18 | Independent security assessment completed | NOT STARTED |
| G19 | Integration sandbox testing completed | NOT STARTED |
| G20 | Conformance testing completed | NOT STARTED |
| G21 | National validation completed | NOT STARTED |
| G22 | Certification obtained where required | NOT STARTED |
| G23 | Clinical governance approval completed | NOT STARTED |
| G24 | Pilot evidence completed | NOT STARTED |
| G25 | Production readiness review completed | NOT STARTED |
| G26 | Production connection authorized | NOT STARTED |

---

# 36. Three Important Status Definitions

## NDHA-Aligned

Means:

> The platform's architecture and design decisions have been intentionally developed with reference to the national digital-health architecture and applicable standards.

It does **not** mean certified.

---

## NDHA-Validated / Certified

Means:

> The responsible national process has evaluated the application and formally confirmed the applicable conformance/certification status.

This must not be claimed without documentary evidence.

---

## Production-Integrated

Means:

> The platform has completed the applicable technical, security, data-protection, interoperability, validation and authorization requirements and is actually connected to the relevant production national service.

This is a later operational state.

---

# 37. What We Must Not Claim Yet

Until formal evidence exists, do not state:

```text
"NDHA certified"
"NDHA approved"
"Government approved"
"Nationally integrated"
"Connected to the national health registry"
"Certified by the Federal Ministry"
"Official national health platform"
```

Instead:

> "Designed for alignment with Nigeria's approved digital-health architecture."

or:

> "Being developed as a standards-based health-support platform capable of future integration with authorized national digital-health infrastructure."

---

# 38. Platform Architectural Commitments

The assurance review confirms the following design commitments.

### Commitment 1

Do not duplicate national master registries.

### Commitment 2

Maintain external identifiers with provenance.

### Commitment 3

Use adapters for national interoperability.

### Commitment 4

Do not make the internal database FHIR-shaped merely for interoperability.

### Commitment 5

Use minimum-necessary data exchange.

### Commitment 6

Keep registry identity separate from platform authorization.

### Commitment 7

Maintain auditability of external exchanges.

### Commitment 8

Design for intermittent connectivity.

### Commitment 9

Do not permit offline clients to manufacture authoritative decisions.

### Commitment 10

Treat privacy and security as production gates.

### Commitment 11

Do not claim national certification before formal certification.

### Commitment 12

Do not assume the current national integration procedure without verification.

---

# 39. Open Questions

The following require authoritative confirmation before production integration.

### OQ-001

What is the current official application process for integrating a private health application with NDHA building blocks?

### OQ-002

Which national office currently owns the operational integration/certification process?

### OQ-003

What are the current certification requirements?

### OQ-004

What are the current sandbox/test endpoints?

### OQ-005

What authentication mechanism is required?

### OQ-006

What API specifications are currently published?

### OQ-007

What Nigerian FHIR implementation guides/profiles are currently required?

### OQ-008

What national identifier services are currently available to approved applications?

### OQ-009

What are the current Health Client Registry integration requirements?

### OQ-010

What are the current Health Facility Registry integration requirements?

### OQ-011

What are the current Healthcare Worker Registry integration requirements?

### OQ-012

What terminology services are currently available?

### OQ-013

What certification evidence must an applicant submit?

### OQ-014

What production monitoring/reporting obligations apply after certification?

---

# 40. Evidence Classification

The project will use the following evidence states:

```text
VERIFIED
PROVISIONAL
DECISION REQUIRED
OPEN / VERIFY
NOT APPLICABLE
```

A requirement should not be implemented as an authoritative national requirement merely because it appears plausible.

---

# 41. Evidence Register

| ID | Evidence | Source | Status |
|---|---|---|---|
| E-NDHA-001 | NDHA establishes interoperable digital-health building blocks | Nigeria Digital Health Architecture | VERIFIED |
| E-NDHA-002 | Public and private applications can integrate | Nigeria Digital Health Architecture | VERIFIED |
| E-NDHA-003 | Integration process includes validation/certification | Nigeria Digital Health Architecture | VERIFIED |
| E-NDHA-004 | Only certified applications may connect to building blocks in production | Nigeria Digital Health Architecture | VERIFIED |
| E-NDHA-005 | Open APIs and standards-based interoperability are architectural principles | Nigeria Digital Health Architecture | VERIFIED |
| E-NDHA-006 | National digital-health coordination currently emphasizes interoperability | Federal Ministry of Health and Social Welfare, Sept. 2026 | VERIFIED |
| E-NDHA-007 | Cybersecurity and data protection are current national digital-health priorities | Federal Ministry of Health and Social Welfare, Sept. 2026 | VERIFIED |
| E-NDHA-008 | Patient confidentiality is a stated national digital-health concern | Federal Ministry of Health and Social Welfare, Sept. 2026 | VERIFIED |
| E-DP-001 | Nigeria Data Protection Act 2023 establishes national data-protection obligations | Nigeria Data Protection Commission | VERIFIED |
| E-DP-002 | GAID 2025 provides implementation requirements under the NDP Act framework | Nigeria Data Protection Commission | VERIFIED |
| E-DP-003 | DPIA requirements apply to high-risk processing | NDP Act / GAID framework | VERIFIED |
| E-DP-004 | Exact platform-specific compliance classification has not yet been determined | Project review | OPEN |
| E-INT-001 | Current operational national integration procedure | Responsible national authority | OPEN / VERIFY |
| E-INT-002 | Current production certification application process | Responsible national authority | OPEN / VERIFY |
| E-INT-003 | Current Nigerian FHIR implementation requirements | Authoritative national specification | OPEN / VERIFY |
| E-INT-004 | Current registry API specifications | Authoritative national specification | OPEN / VERIFY |

---

# 42. Evidence Sources

The primary evidence sources for this document are:

1. Nigeria Digital Health Architecture (NDHA)
2. Nigeria Digital Health Initiative official documentation
3. Federal Ministry of Health and Social Welfare official publications
4. Nigeria Data Protection Commission official publications
5. Applicable Nigerian laws and regulations
6. Authoritative national technical specifications when published

Secondary technical standards may include:

- HL7 FHIR;
- OpenAPI;
- OWASP;
- NIST;
- WCAG;
- PostgreSQL;
- Django.

International technical standards provide engineering guidance but do not replace Nigerian legal or national interoperability requirements.

---

# 43. Current Architecture Assurance Position

After review:

```text
INTERNAL ARCHITECTURE
        │
        ▼
CONDITIONALLY READY FOR DEVELOPMENT
```

but:

```text
NATIONAL PRODUCTION INTEGRATION
        │
        ▼
NOT READY
```

The missing items are primarily:

- formal national integration pathway;
- current certification process;
- current technical specifications;
- authoritative identifier integration;
- FHIR/profile mapping;
- security validation;
- data-protection assessment;
- DPIA;
- testing;
- certification;
- operational authorization.

---

# 44. Architecture Assurance Gate

The following gate must be completed before the database design is considered final.

## Gate A — National Alignment

Questions:

```text
Are we duplicating a national service?
Are we using an authoritative identifier incorrectly?
Are we claiming authority we do not possess?
Are we assuming an integration standard without evidence?
```

Status:

**PASS WITH OPEN ITEMS**

---

## Gate B — Interoperability

Questions:

```text
Can our internal model remain independent from FHIR?
Can external mappings be versioned?
Can identifiers retain provenance?
Can integrations fail safely?
```

Status:

**DESIGNED / REQUIRES IMPLEMENTATION**

---

## Gate C — Privacy

Questions:

```text
Is the lawful basis defined?
Is data minimized?
Is access controlled?
Is a DPIA planned?
Are processors governed?
```

Status:

**DESIGNED / DPIA REQUIRED**

---

## Gate D — Security

Questions:

```text
Is authentication defined?
Is authorization contextual?
Is BOLA addressed?
Are external integrations isolated?
Is auditability defined?
```

Status:

**DESIGNED / TESTING REQUIRED**

---

## Gate E — Operational Readiness

Questions:

```text
Can the platform operate during partner outages?
Can it recover safely?
Can it detect duplicate messages?
Can it monitor integrations?
Can it respond to incidents?
```

Status:

**DESIGNED / IMPLEMENTATION REQUIRED**

---

# 45. Database Design Consequences

The assurance review does not require the internal database to become a national registry.

However, the database design must preserve the ability to:

```text
Store authoritative external identifiers
Store source/provenance
Store verification state
Store identifier validity periods
Store external references
Track integration events
Track version history
Support contextual authorization
Support audit
```

The existing database design must therefore be reviewed against this document before it is frozen.

---

# 46. API Design Consequences

The API specification must eventually support:

```text
Internal APIs
        +
Partner APIs
        +
FHIR/Interoperability Adapters
        +
Authentication
        +
Authorization
        +
Audit
        +
Idempotency
        +
Versioning
```

National integration APIs should not be embedded directly into unrelated domain logic.

---

# 47. Deployment Consequences

Production national integration requires separate environments:

```text
Development
      ↓
Testing
      ↓
Staging
      ↓
Integration Sandbox
      ↓
Validation
      ↓
Certification
      ↓
Production
```

Production credentials and production national endpoints must never be used during ordinary development.

---

# 48. Governance Consequences

Before production integration, the project must identify accountable owners for:

```text
Platform Governance
Clinical Governance
Data Protection
Information Security
Interoperability
Integration Management
Incident Response
Patient Complaints
Funding Governance
Partner Management
Operational Support
```

Technical administrators must not automatically receive authority over clinical, funding or governance decisions.

---

# 49. Decision Register Entries

The following decisions are now required.

### DEC-NDHA-001

**Decision:** Current national integration/certification authority and procedure.

**Status:** OPEN / VERIFY

---

### DEC-NDHA-002

**Decision:** Applicable national identifier services.

**Status:** OPEN / VERIFY

---

### DEC-NDHA-003

**Decision:** Applicable Nigerian FHIR profiles and implementation guides.

**Status:** OPEN / VERIFY

---

### DEC-NDHA-004

**Decision:** Registry integration scope for patient, facility and healthcare-worker identities.

**Status:** OPEN / VERIFY

---

### DEC-NDHA-005

**Decision:** Production certification evidence package.

**Status:** OPEN / VERIFY

---

### DEC-NDHA-006

**Decision:** Data-protection compliance classification and obligations for the platform.

**Status:** DECISION REQUIRED

---

# 50. What This Document Prevents

This document is specifically intended to prevent the following engineering mistakes:

```text
"Let's just create our own national patient ID."

"Let's make our own facility registry."

"Let's store NIN and call it the health ID."

"Let's make our database FHIR."

"Let's connect directly to a national production API."

"Let's claim NDHA compliance because our API works."

"Let's use consent as the answer to every privacy question."

"Let's build offline approval so users can keep working."

"Let's assume an old government integration process is still current."
```

Each of these would require evidence and/or formal authority before implementation.

---

# 51. Current Project Statement

The project's accurate public technical statement at this stage is:

> **The NCD Patient Safety Platform is being developed as a standards-based, privacy-conscious healthcare-support and patient-safety platform designed for compatibility with Nigeria's emerging digital-health ecosystem. It is intended to integrate with authoritative national services where appropriate, subject to applicable technical, legal, security, interoperability, validation and certification requirements.**

This statement does not claim government endorsement or national certification.

---

# 52. Next Assurance Step

This document is not the end of the assurance review.

The next step is:

## **FORMAL ARCHITECTURE ASSURANCE GATE**

We will review the existing:

```text
09 National Alignment
10 System Architecture
11 Database Design
12 API Specification
13 Risk Register
```

against the verified findings in this document.

The objective is to identify:

```text
KEEP
CHANGE
REMOVE
ADD
OPEN QUESTION
DECISION REQUIRED
```

before database implementation proceeds.

---

# 53. Status

**Document:** NDHA Integration Readiness v0.1

**National alignment:** VERIFIED DIRECTION

**Integration authority:** OPEN / VERIFY

**Technical requirements:** PARTIALLY VERIFIED

**Certification pathway:** OPEN / VERIFY

**Data protection:** VERIFIED LEGAL FRAMEWORK / IMPLEMENTATION REQUIRED

**DPIA:** REQUIRED / NOT STARTED

**Security testing:** REQUIRED / NOT STARTED

**FHIR implementation mapping:** OPEN / VERIFY

**Registry integration:** OPEN / VERIFY

**Production integration:** NOT READY

**Architecture assurance:** PASS WITH OPEN ITEMS

**Next gate:** FORMAL ARCHITECTURE ASSURANCE REVIEW
