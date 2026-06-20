# Delivery Management System

A Flask web application for managing local delivery operations: orders, drivers, shops, commissions, and financial ledgers. Built for day-to-day use by operators, drivers, and administrators.

## Features

- **Multi-role access** — Admin, operator, and driver dashboards
- **Order workflow** — Pending → Assigned → Accepted → Picked Up → Delivered
- **Driver accounting** — Commission tracking with cash vs. paid order handling
- **Shop & place management** — Shops linked to areas with route-based commissions
- **Activity logging** — Audit trail for key actions
- **Arabic operator UI** — Operator section fully localized (RTL)
- **Safe database migrations** — Schema changes via Flask-Migrate (no manual DB edits)

## Tech Stack

- Python, Flask
- SQLAlchemy + SQLite
- Flask-Migrate (Alembic)
- Bootstrap 5, Jinja2 templates

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up the database

```bash
python manage.py db upgrade
python manage.py seed
```

> On startup, `run.py` also runs migrations and seeds default data if missing.

### 3. Run the app

```bash
python run.py
```

Open [http://localhost:5006](http://localhost:5006)

## Default Users

| Role     | Username  | Password   |
|----------|-----------|------------|
| Admin    | `admin`   | `admin123` |
| Operator | `operator`| `op123`    |
| Driver   | `driver1` | `d123`     |

Change these passwords before deploying to production.

## Database Migrations

Edit schema in `app/models.py`, then:

```bash
python manage.py db migrate -m "describe your change"
python manage.py db upgrade
```

Never edit `delivery.db` manually. See `model.py` for the full workflow.

### Useful commands

```bash
python manage.py db current     # show current migration
python manage.py db history     # list migrations
python manage.py seed           # insert default settings/users
python manage.py db downgrade   # undo last migration
```

## Project Structure

```
├── app/
│   ├── models.py       # Database models (edit here for schema changes)
│   ├── admin.py        # Admin routes
│   ├── operator.py     # Operator routes
│   ├── driver.py       # Driver routes
│   ├── auth.py         # Login / logout
│   ├── accounting.py   # Commission & ledger logic
│   └── templates/      # HTML templates
├── migrations/         # Alembic migration files
├── manage.py           # CLI for DB and seeding
├── model.py            # Model exports + migration docs
├── run.py              # Application entry point
├── config.py           # App configuration
└── requirements.txt
```

## Production Notes

- Set a strong `SECRET_KEY` in `config.py`
- Use a production WSGI server (e.g. Gunicorn) instead of `app.run()`
- Replace default user passwords
- Consider PostgreSQL instead of SQLite for multi-user production loads

## License

Private / internal use unless otherwise specified.
