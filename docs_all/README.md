# Coal LIMS Documentation Index

> Last updated: 2026-02-15

## Quick Start

| Goal | Document |
|------|----------|
| Set up dev environment | [Developer Onboarding Guide](LIMS_-_Developer_Onboarding_Guide.md) |
| Understand architecture | [System Architecture](LIMS_-_System_Architecture.md) |
| Use the API | [API Documentation](LIMS_-_API_Documentation.md) |
| Deploy to production | [Production Deployment Guide](🚀_LIMS_-_Production_Deployment_Guide.md) |
| Database tables & ER diagram | [Database Schema](Database_Schema.md) |
| User/Admin workflows | [User & Admin Guide](User_Admin_Guide.md) |

---

## 1. Architecture & Design

| Document | Description | Status |
|----------|-------------|--------|
| [System Architecture](LIMS_-_System_Architecture.md) | Multi-lab architecture, BaseLab pattern, ADRs, Mermaid diagrams | Current |
| [Database Schema](Database_Schema.md) | 46 models, all columns, relationships, Mermaid ER diagram | Current |
| [Laboratory Information Management System](LIMS_-_Laboratory_Information_Management_System.md) | Full system overview (4 labs, workflow, features) | Current |
| [Copilot Instructions](Copilot_Instructions_for_LIMS.md) | AI assistant context (architecture, conventions, workflows) | Current |

## 2. Development

| Document | Description | Status |
|----------|-------------|--------|
| [Developer Onboarding Guide](LIMS_-_Developer_Onboarding_Guide.md) | Environment setup, project structure, coding standards, Git workflow | Current |
| [Testing Guide](Testing_Guide.md) | Test strategy, pytest, fixtures, coverage (89%), CI/CD pipeline | Current |
| [Docstring & Comment Standard](LIMS_-_Docstring_&_Comment_Standard.md) | Code documentation conventions (Google-style) | Current |
| [Template Macros Guide](Template_Macros_-_Хэрэглэх_заавар.md) | Jinja2 form/table macros usage | Outdated |

## 3. API & Integration

| Document | Description | Status |
|----------|-------------|--------|
| [API Documentation](LIMS_-_API_Documentation.md) | 70+ REST endpoints, response format, rate limits, error codes | Current |

## 4. Security & Compliance

| Document | Description | Status |
|----------|-------------|--------|
| [Security Documentation](АЮУЛГҮЙ_БАЙДЛЫН_БАРИМТ_БИЧИГ.md) | SQL injection, rate limiting, CSRF, session security, XSS | Current |
| [ISO 17025 Compliance](ISO_17025_БАРИМТ_БИЧИГ.md) | ISO 17025 implementation status (65% complete) | Current |
| [Role & Permissions](LIMS_-_ROLE_PERMISSIONS_LOG.md) | Role-based access control (admin, senior, chemist, manager) | Current |
| [Precision & Repeatability](PRECISION_&_REPEATABILITY_БАРИМТ_БИЧИГ.md) | Analysis tolerance limits, repeatability rules | Current |

## 5. Deployment & Operations

| Document | Description | Status |
|----------|-------------|--------|
| [Production Deployment Guide](🚀_LIMS_-_Production_Deployment_Guide.md) | Gunicorn, Nginx, Docker, environment config | Current |
| [Operations Runbook](LIMS_-_Operations_Runbook.md) | Daily ops, backup/restore, troubleshooting, rollback, SSL, escalation | Current |
| [Performance & Optimization](Performance_Optimization_Guide.md) | DB pooling, monitoring, load testing, caching, scaling | Current |
| [Production Readiness Report](LIMS_Production_Readiness_Report.md) | Security audit score 95/100, deployment checklist | Current |
| [Windows Backup Setup](Windows_Task_Scheduler_-_Автомат_Backup_Тохиргоо.md) | Windows Task Scheduler automated backup config | Current |
| [Monitoring Stack](LIMS_-_Monitoring_Stack.md) | Quick reference (see Performance Guide for details) | Current |
| [Performance Testing](Performance_Testing.md) | Quick reference (see Performance Guide for details) | Current |

## 6. User Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [User & Admin Guide](User_Admin_Guide.md) | Workflows for chemist, senior, manager, admin roles + FAQ | Current |
| [Video Tutorial Scripts](LIMS_-_Video_Tutorial_Scripts.md) | Tutorial script templates | Incomplete |

## 7. Code Audit Reports (2026-02-05)

| Document | Scope |
|----------|-------|
| [Full Audit Summary](Coal_LIMS_-_Бүрэн_код_шалгалтын_тайлан.md) | Complete code audit summary |
| [Sample Registration](Sample_Registration_&_List_Code_Audit.md) | Sample CRUD, lab_type filter, pagination |
| [Analysis Workspace](Analysis_Workspace_Code_Audit.md) | N+1 queries, API format, role access |
| [Equipment System](Equipment_Code_Audit.md) | Equipment CRUD, audit logging, SQL injection |
| [Chemicals System](Chemicals_Code_Audit.md) | Chemical inventory, pagination, boolean filter |
| [Reports & Dashboard](Reports_&_Dashboard_Code_Audit.md) | Dashboard security, shift-aware calculations |
| [Role & Authentication](Role_&_Authentication_Code_Audit.md) | Admin protection, audit logging, rate limiting |
| [models.py Audit](models.py_Detailed_Audit.md) | HashableMixin, unused code removal |
| [constants.py Audit](constants.py_Audit.md) | Consolidation, unused constants |
| [Code Duplication](Code_Duplication_&_Unused_Code_Audit.md) | to_float() consolidation, 60 lines eliminated |
| [Equipment System (detailed)](ТОНОГ_ТӨХӨӨРӨМЖИЙН_СИСТЕМИЙН_АУДИТ_ТАЙЛАН.md) | Equipment journals, spare parts, calibration |
| [Production Audit Log](LIMS_-_Production_Audit_Log.md) | Production environment audit trail |

## 8. Other

| Document | Description | Status |
|----------|-------------|--------|
| [Changelog](CHANGELOG_-_LIMS_Сайжруулалтууд.md) | Full change history (2025-11 ~ 2026-02) | Current |
| [License Protection](LIMS_Лиценз_Хамгаалалтын_Систем.md) | License system design | Outdated |
| [System Comparison](LIMS_Системийн_Мэргэжлийн_Харьцуулалт.md) | LIMS vs Zobo comparison | Outdated |
| [Mobile UI](COAL_LIMS_-_Mobile_Responsive_UI_Implementation.md) | Mobile responsive implementation | Outdated |
| [Full Analysis (Jan)](COAL_LIMS_-_БҮРЭН_ДЭЛГЭРЭНГҮЙ_ДҮН_ШИНЖИЛГЭЭ.md) | Early comprehensive analysis | Outdated |
| [3-Lab Review](3_лабын_код_шалгалт_ба_төлөвлөгөө.md) | Initial 3-lab code review plan | Outdated |
| [Code Audit (Dec)](КОД_АУДИТЫН_ТАЙЛАН.md) | Early code audit report | Outdated |
| [Technical Doc (Dec)](ТЕХНИКИЙН_БАРИМТ_БИЧИГ.md) | Early technical documentation | Outdated |

---

## Archived

Work logs, session logs, and date-specific changelogs have been moved to [archived/](archived/).
25 files archived (daily logs, coverage reports, session notes).
