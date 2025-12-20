# Copilot Instructions for Coal LIMS

## Project Overview
- **Coal LIMS** is a laboratory information management system for coal analysis, developed by Gantulga, designed to comply with **ISO 17025** standards.
- Main backend: **Flask** (3.1+), ORM: **SQLAlchemy**, migrations: **Alembic**.
- Frontend: **Jinja2** templates, **Bootstrap 5**, **Vanilla JS**, **Chart.js**.
- Data: SQLite (dev), PostgreSQL (prod).

## Architecture & Key Patterns
- **app/** contains core modules: `models.py` (ORM), `forms.py` (Flask-WTF), `services/` (business logic), `routes/` (Flask blueprints), `schemas/` (validation), `utils/` (helpers).
- **Templates** use Jinja2 macros for forms/tables. See `app/templates/macros/README.md` for macro usage and examples.
- **Role-based access**: User roles (admin, senior, analyst, etc.) enforced in routes/services.
- **Config**: Use `config.py` and `.env` for environment variables. See README for required keys.
- **Seed scripts**: Use `flask seed-analysis-types`, `flask seed-sample-types`, `flask seed-error-reasons` for initial data.

## Developer Workflows
- **Setup**: `python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt`
- **Run**: `python run.py` (dev) or `flask run` (debug)
- **Migrations**: `flask db upgrade`
- **Testing**: `pytest` (all), `pytest --cov=app --cov-report=html` (coverage)
- **Lint/Format**: `black app/ tests/`, `flake8 app/ tests/`, `mypy app/`
- **Pre-commit**: `pre-commit install; pre-commit run --all-files`
- **Deployment**: Gunicorn (`gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"`), Docker (`docker-compose up -d`)

## Conventions & Patterns
- **Google-style docstrings** and **type hints** required for all functions.
- **Comments** in Mongolian, **commits** in English.
- **Templates**: Always use macros for forms/tables to reduce duplication (see macro README for examples).
- **Security**: CSRF, XSS, rate limiting, session security, and audit logging are enforced (see `SECURITY_CHECKLIST.md`).
- **API**: RESTful endpoints documented at `/api/docs` (Swagger UI). Key endpoints: `/api/samples/data`, `/api/analysis/save_results`, `/api/equipment`.

## Integration Points
- **Email**: Flask-Mail, configure via `.env`.
- **Excel Export**: openpyxl for reports.
- **Charts**: Chart.js for QC dashboards.
- **Static/Uploads**: Use `instance/uploads/certificates` for file uploads.

## Examples
- **Jinja2 macro usage**:
  `{% from 'macros/form_helpers.html' import render_field %}`
  `{{ render_field(form.username) }}`
- **Seed initial data**:
  `flask seed-analysis-types; flask seed-sample-types; flask seed-error-reasons`
- **Run tests with coverage**:
  `pytest --cov=app --cov-report=html`

## References
- See `README.md` for setup, workflows, and architecture.
- See `app/templates/macros/README.md` for template macro usage.
- See `SECURITY_CHECKLIST.md` for security practices.

---

**Update this file as project conventions evolve.**
