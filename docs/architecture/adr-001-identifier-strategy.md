# ADR-001 — Identifier Strategy

**Project:** NCD Patient Safety Platform
**Decision:** Internal BIGINT + Public UUID + External Identifier Provenance
**Status:** Accepted for implementation
**Version:** 0.1
**Date:** September 2026

---

## 1. Decision

The platform will use a **hybrid identifier strategy**.

### Internal relational identifiers

Use PostgreSQL/Django integer identifiers:

```text
BIGINT
```

for internal primary keys and foreign-key relationships.

### Public/API identifiers

Use UUIDs for externally exposed resource identifiers:

```text
UUID
```

These identifiers will be used for API-facing resources and other contexts where exposing sequential database identifiers is undesirable.

### External/business identifiers

External identifiers received from authorized systems will be stored separately with provenance:

```text
Identifier
├── System
├── Value
├── Type
├── Source
├── Verification Status
└── Provenance
```

The platform will not replace authoritative external identifiers with internal identifiers.

---

# 2. Context

The platform is expected to handle potentially large volumes of:

* patients;
* care-support cases;
* clinical events;
* patient-safety events;
* funding applications;
* payments;
* notifications;
* audit events;
* integration events.

The identifier strategy therefore needs to balance:

* database storage;
* index size;
* query performance;
* API security;
* interoperability;
* external integration;
* long-term scalability.

---

# 3. Storage Evidence

The project's PostgreSQL 18.6 environment was directly tested.

Measured column sizes:

```text
BIGINT = 8 bytes
UUID   = 16 bytes
```

Therefore a UUID requires twice the raw storage of a BIGINT identifier.

The difference becomes increasingly relevant when identifiers are repeated in:

* primary keys;
* foreign keys;
* indexes;
* composite indexes;
* high-volume event tables.

The project therefore will not use UUIDs indiscriminately for every internal relational key.

---

# 4. Why BIGINT for Internal Keys

BIGINT provides:

* compact storage;
* smaller indexes than UUID;
* efficient relational joins;
* native PostgreSQL support;
* simple Django integration;
* adequate numeric range for the expected application.

The internal identifier is an implementation detail.

It does not need to serve as the public identity of a resource.

---

# 5. Why UUID for Public Identifiers

Externally exposed identifiers should not unnecessarily reveal sequential database structure.

For example, the API should avoid relying on:

```text
/patients/1001
/patients/1002
/patients/1003
```

as the public resource identity.

Instead:

```text
/patients/<opaque-uuid>
```

may be used.

However:

> UUIDs are not an authorization mechanism.

Object-level authorization must still be enforced on every protected resource.

---

# 6. Resource Pattern

Major externally addressable entities should follow the pattern:

```text
Patient
├── id
│   └── BIGINT
└── public_id
    └── UUID
```

Likewise:

```text
CareSupportCase
├── id BIGINT
└── public_id UUID

FundingApplication
├── id BIGINT
└── public_id UUID

SafetyEvent
├── id BIGINT
└── public_id UUID

Payment
├── id BIGINT
└── public_id UUID
```

Not every internal-only table necessarily requires a public UUID.

The requirement for a public identifier will be determined by whether the resource crosses an API, integration, audit, or external workflow boundary.

---

# 7. External Identifiers

The platform must distinguish its own identifiers from identifiers belonging to external systems.

Example:

```text
Patient
│
├── Internal ID
│   └── BIGINT
│
├── Public ID
│   └── UUID
│
└── External Identifiers
    ├── System
    ├── Identifier
    ├── Type
    ├── Issuer
    └── Provenance
```

This allows the platform to integrate with authorized national, government, healthcare, insurance, NGO or other systems without assuming that all systems use the same identifier format.

---

# 8. Interoperability Principle

The platform's internal database identifier strategy must not dictate the identifier strategy of external systems.

External identifiers must be preserved where legitimately received.

The platform should maintain mappings such as:

```text
External System Identifier
          ↓
Identifier Mapping
          ↓
Internal Patient / Resource
```

The original external identifier must remain attributable to its source.

---

# 9. FHIR Compatibility Principle

FHIR distinguishes a resource's logical identity from business identifiers.

Therefore the platform does not need to make its PostgreSQL primary key identical to every external healthcare identifier.

Conceptually:

```text
Platform public_id
       ↓
FHIR Resource.id

External/business identifier
       ↓
FHIR Resource.identifier
```

The exact FHIR mapping will be defined in the interoperability specification.

---

# 10. Identity User Model

The current Django identity model already uses:

```text
identity_user.id
BIGINT
```

This migration has been successfully applied to PostgreSQL.

The current BIGINT primary key will therefore remain.

If the application requires an externally exposed user identifier, a separate UUID field may be introduced later:

```text
User
├── id BIGINT
└── public_id UUID UNIQUE
```

This decision avoids unnecessary migration risk to the foundational authentication model.

---

# 11. UUID Version

The current development environment is:

```text
Python 3.12.3
```

Native Python support was verified for:

```text
UUID4
```

Native `uuid.uuid7()` is not available in this Python version.

Therefore the project will **not introduce a UUID7 dependency merely to satisfy the identifier strategy**.

If UUID7 becomes desirable later, it will require a separate architecture decision considering:

* dependency;
* PostgreSQL support;
* indexing;
* ordering characteristics;
* operational impact;
* interoperability requirements.

Until then, UUID4 is the provisional public UUID implementation.

---

# 12. Security Boundary

Public UUIDs provide opaque identifiers but do not replace:

* authentication;
* authorization;
* object-level authorization;
* role-based access control;
* contextual access control;
* rate limiting;
* audit logging;
* input validation.

The security model remains:

```text
Authentication
      ↓
Authorization
      ↓
Object-Level Authorization
      ↓
Business Rules
      ↓
Audit
```

---

# 13. Performance and Storage Principle

The project will avoid unnecessary duplication of UUIDs in high-volume internal tables.

For example, an internal event table may use:

```text
event.id BIGINT
```

while referencing:

```text
case.id BIGINT
```

If the event itself must be exposed externally, it may additionally have:

```text
event.public_id UUID
```

This keeps internal relational structures compact while allowing safe external resource identification.

---

# 14. Uniqueness Requirements

Public identifiers must be unique within their resource namespace.

Example:

```text
public_id UUID UNIQUE
```

External identifiers must be unique only according to the rules of their issuing system.

The platform must not assume that an identifier value is globally unique without considering:

```text
System
+
Type
+
Value
```

---

# 15. Audit Requirements

Audit records should be capable of referencing both:

```text
Internal resource identity
```

and, where appropriate:

```text
Public/external resource identity
```

Audit records must preserve provenance and must not depend exclusively on mutable display names.

---

# 16. Consequences

### Benefits

* reduced internal key and index storage;
* efficient PostgreSQL joins;
* opaque API-facing identifiers;
* clearer separation between implementation and external identity;
* better interoperability flexibility;
* preservation of external identifiers;
* reduced migration pressure on the authentication model.

### Costs

* some entities will have two identifiers;
* application code must clearly distinguish internal and public IDs;
* additional uniqueness constraints are required;
* API serializers must expose the correct identifier;
* identifier mapping requires careful design.

---

# 17. Implementation Rule

Developers must not casually expose internal BIGINT IDs through public APIs.

Every API resource must explicitly define whether it exposes:

```text
public_id
```

or another authorized external identifier.

Internal database IDs may remain available inside trusted application boundaries where appropriate.

---

# 18. Examples

### Patient

```text
Database:
id = 1045821

Public:
public_id = <UUID>

External:
system = authorized-system
value = external identifier
```

### Case

```text
Database:
id = 782143

Public:
public_id = <UUID>
```

### Funding Application

```text
Database:
id = 551920

Public:
public_id = <UUID>
```

These examples are illustrative only.

---

# 19. Decision Boundary

This ADR does not decide:

* national patient identifier policy;
* government registry identifiers;
* NHIA identifiers;
* facility identifiers;
* healthcare professional identifiers;
* FHIR resource mapping details;
* payment-provider transaction identifiers.

Those belong to their respective governance and interoperability decisions.

---

# 20. Final Decision

The NCD Patient Safety Platform will use:

```text
┌───────────────────────────────────────┐
│ INTERNAL DATABASE                     │
│                                       │
│ BIGINT primary keys                   │
│ BIGINT foreign keys                   │
└───────────────────────────────────────┘

                  +

┌───────────────────────────────────────┐
│ PUBLIC / API RESOURCE IDENTITY        │
│                                       │
│ UUID                                  │
└───────────────────────────────────────┘

                  +

┌───────────────────────────────────────┐
│ EXTERNAL IDENTIFIERS                  │
│                                       │
│ System + Value + Type + Provenance    │
└───────────────────────────────────────┘
```

This is the approved identifier direction for the current architecture.

---

# 21. Review Trigger

This ADR must be revisited if:

* national identifier requirements change;
* the interoperability architecture requires a different identifier model;
* PostgreSQL architecture changes;
* UUID7 becomes operationally justified;
* external partners require a different identifier contract;
* database scale demonstrates a material performance issue;
* regulatory requirements establish a mandatory identifier standard.

**Status: ACCEPTED FOR IMPLEMENTATION**
