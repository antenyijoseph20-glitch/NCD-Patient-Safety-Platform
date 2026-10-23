# Team A — Clinical, Patient & Care-Delivery Stream

**Stream Lead:** Team A  
**Milestone:** M1 Delivery — Foundational Patient & Clinical Core  
**Branch:** `feature/team-a/clinical-patient-core`  
**Status:** Implemented & Verified  

---

## 1. Scope Delivered

Team A has implemented and tested the core clinical and patient-safety domain models in alignment with:
- `docs/database/11-database-design.md`
- `docs/architecture/adr-001-identifier-strategy.md`

### Applications & Entities Implemented:

1. **`apps.patients`**
   - **`Patient`**: Demographics, blood group, genotype, status lifecycle, `UUID` public ID, and optional `User` link (supports self-registered and caregiver-assisted patients).
   - **`PatientContact`**: Multi-channel contact points (phone, email, physical address, next-of-kin, emergency contact).
   - **`CaregiverRelationship`**: Delegated authority matrix (`can_view_records`, `can_manage_care`, `can_apply_funding`) protected against cascade deletion.
   - **`ExternalIdentifier`**: Provenance tracking for national (NIN, NHIA) and external hospital EMR identifiers.

2. **`apps.clinical_need`**
   - **`ClinicalNeed`**: Diagnosis, ICD-10 code mapping, severity levels, and clinical status state machine.
   - **`ClinicalVerification`**: Clinical governance audit trail certifying that only qualified `HealthcareProfessional`s at registered `Facility`s can verify needs.
   - **`ClinicalEvidence`**: Immutable document provenance with SHA-256 checksums (prescriptions, pathology, radiology).

3. **`apps.cases`**
   - **`CareSupportCase`**: Care coordination backbone linking Patient and ClinicalNeed, tracking lifecycle status from `OPEN` to `FUNDING_ELIGIBLE` and `ASSISTANCE_ACTIVE`.
   - **`CaseAssignment`**: Separation between patient ownership and staff operational assignment (Case Officer, Clinical Lead, Liaison, Auditor).

4. **`apps.safety`**
   - **`SafetyEvent`**: Adverse event and patient safety incident reporting with severity triage, immediate remediation recording, and case linking.

---

## 2. Interface Contract for Team B (Funding & Finance Stream)

Team B is responsible for Funding, Payments, and Financial Governance. The interface contract between Team A and Team B is defined as follows:

```text
┌────────────────────────────────┐
│      apps.cases.CareSupportCase│
│      (Owned by Team A)         │
│  - id: BIGINT                  │
│  - public_id: UUID             │
│  - status: FUNDING_ELIGIBLE    │
└───────────────▲────────────────┘
                │
                │ on_delete=models.PROTECT
                │
┌───────────────┴────────────────┐
│  apps.funding.FundingApplication│
│  (Owned by Team B)             │
│  - case: ForeignKey            │
│  - requested_amount: Decimal   │
│  - status: SUBMITTED           │
└────────────────────────────────┘
```

### Handoff Requirements for Team B:
1. **Foreign Key Reference:**
   ```python
   case = models.ForeignKey(
       'cases.CareSupportCase',
       on_delete=models.PROTECT,
       related_name='funding_applications',
   )
   ```
2. **Pre-Funding Eligibility Rule:**
   Before a `FundingApplication` can be submitted, `case.status` must be `CareSupportCase.Status.FUNDING_ELIGIBLE`, and `case.primary_clinical_need.verifications.filter(status='VERIFIED').exists()` must evaluate to `True`.
3. **Migration Independence:**
   Because Team B creates migrations inside `apps/funding/migrations/`, it will depend cleanly on `cases.0001_initial` without merge conflicts.

---

## 3. Test Coverage Summary

- **Total Test Cases Running:** 49 tests
- **Applications Covered:** `organizations`, `patients`, `clinical_need`, `cases`, `safety`
- **End-to-End Test:** `IntegrationWorkflowTests.test_end_to_end_patient_care_case_workflow` validates complete traversal from patient intake to clinical verification, case management, and safety incident reporting.
