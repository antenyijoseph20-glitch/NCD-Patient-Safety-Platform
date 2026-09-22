# NCD Patient Safety Platform

A standards-based digital platform designed to support safe, coordinated care and assistance for people living with noncommunicable diseases (NCDs).

## Project Status

**Current milestone:** M1 — Secure Platform Foundation

The project is currently in the foundational development stage. Core architecture, governance, clinical safety, data protection, security, database, API, and implementation requirements have been defined before application development.

## Core Principles

- Patient safety first
- Privacy by design
- Security by design
- Least privilege
- Separation of duties
- Clinical authority remains with qualified professionals
- Funding approval is separate from payment execution
- Full accountability and auditability
- Evidence before assumption
- Interoperability over duplication
- Human oversight for high-impact decisions

## Technical Direction

The initial implementation uses a modular Django monolith with:

- Python
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Object storage
- REST APIs
- OpenAPI

The architecture is designed to support future interoperability with appropriate Nigerian health-information systems and approved external partners.

## Documentation

Project documentation is maintained under `docs/`.

Important documentation includes:

- Project Charter
- Stakeholders and Roles
- Product Requirements
- Patient and Caregiver Journeys
- Clinical Governance
- Funding Governance
- Data Governance
- Security Architecture
- National Alignment
- System Architecture
- Database Design
- API Specification
- Risk Register
- Roadmap

## Development Rule

> Verify before assuming. Document before implementing. Design security before deployment. Protect patients before optimizing features.

## Repository Structure

```text
NCD-Patient-Safety-Platform/
├── docs/
├── scripts/
├── src/
│   └── apps/
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── pyproject.toml
