# Restaurant & Food Delivery Management System

A backend system built with **FastAPI** to run a complete food delivery
platform — restaurants and their menus, customer carts and orders, coupons,
delivery partners, live order tracking, payments, refunds, and reviews.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (PostgreSQL also supported) |
| Validation | Pydantic |
| Authentication | JWT (real access + refresh tokens) |
| Migrations | Alembic |
| Caching / Broker | Redis (caching + Celery broker/backend) |
| Async work | Celery (worker only — no scheduled beat job) |
| PDF generation | ReportLab |
| Excel export | openpyxl |
| Live updates | WebSocket |
| Geocoding | OpenStreetMap Nominatim (free, no API key) |
| Distance calculation | Haversine formula (local, no external call) |
| Testing | Pytest |
| CI/CD | GitHub Actions |

---

## Features by Level

### ✅ Level 1 – Authentication & Authorization
5 roles: Admin, Restaurant Owner, Restaurant Staff, Delivery Partner,
Customer. Real JWT access + refresh tokens, change-password, account
activation/deactivation. Admin is created automatically on startup and
registers Restaurant Owners directly; Restaurant Owners register their own
Restaurant Staff. Both Customer and Delivery Partner are purely self-service
— no staff-created path, matching how real food delivery and gig-economy
platforms actually work.

### ✅ Level 2 – Restaurant Management
Full CRUD, opening/closing hours validated at both schema and database level
(including on partial updates, correctly merging old and new values before
checking), ownership scoping so an owner can only manage their own
restaurant.

### ✅ Level 3 – Menu & Food Item Management
Full CRUD, price validation, availability toggling, ownership scoping down
to the specific restaurant a menu item belongs to. Soft delete via the
availability flag, since a menu item may already be referenced by real,
permanent order history.

### ✅ Level 4 – Customer & Address Management
Customer registration is genuinely public and self-service — no hybrid
staff-created path, since nothing about ordering food requires someone else
to sign a customer up. Addresses support multiple entries per customer with
exactly one default (enforced by explicitly un-defaulting every other
address whenever a new one is marked default), and real geocoding via
OpenStreetMap's free Nominatim service converts each address into genuine
latitude/longitude coordinates.

### ✅ Level 5 – Cart Management
Add/update/remove/clear, live subtotal calculation. The one-restaurant-per-
cart rule is enforced through a real lock mechanism — the cart remembers
which restaurant it belongs to the moment the first item is added, and
releases that lock automatically once the cart is fully emptied.

### ✅ Level 6 – Coupon & Offers
Percentage and flat discounts, minimum order value, maximum discount cap,
usage limits, and a real one-customer-one-use restriction checked against
that customer's own past orders.

### ✅ Level 7 – Order Management
Automatic total calculation matching the exact formula (subtotal + tax +
delivery fee − discount), restaurant-must-be-open check, item-availability
re-check at the moment of ordering (not just when added to cart), and each
order item permanently locks in its own name and price at the time of
purchase.

### ✅ Level 8 – Delivery Partner Management
Genuine self-registration with real vehicle details, availability toggling,
and a real conflicting-delivery protection — a partner currently on an
active delivery cannot change their own availability status at all (not
just "back to available," any change), preventing a rider from abandoning a
delivery mid-route.

### ✅ Level 9 – Order Tracking
Every real status change writes a permanent history entry automatically, as
a side effect of the status update itself — not a separate manual action.
Completed or cancelled orders are permanently locked from further updates.

### ✅ Level 10 – Payment Management
UPI/Card/Wallet/Cash on Delivery, with a genuine conditional validation rule
— every method except cash on delivery requires a real transaction
reference, and duplicate transaction references are blocked at both the
schema and database level.

### ✅ Level 11 – Cancellation & Refund
Only cancelled orders can be refunded, the refund amount is capped against
what was actually paid, and a real database constraint prevents the same
order from ever being refunded twice.

### ✅ Level 12 – Reviews & Ratings
One combined review per order, covering both the restaurant/food experience
and the delivery experience separately — only orders that have genuinely
reached "Delivered" can be reviewed, and never twice.

### ✅ Level 13 – Search, Filtering & Pagination
Restaurants (city, cuisine, status, a real calculated average rating, and
delivery radius as an honest proxy for delivery time, since no live ETA data
exists), Food Items (category, price range, vegetarian, availability),
Orders (status, payment status, restaurant, date range) — `page`, `limit`,
`sort_by`, `sort_order` throughout.

### ✅ Level 14 – Notifications & Background Tasks
All 8 required notification types, sent through real Celery tasks — order
placed (with PDF invoice attached), order accepted/preparing/ready, driver
assigned, out for delivery, delivered, payment success, refund processed.

### ✅ Level 15 – Restaurant Dashboard
All 9 metrics for restaurant owners — today's/pending/completed/cancelled
orders, today's and monthly revenue, most-ordered food, average rating,
total customers — scoped so an owner only ever sees their own restaurant's
numbers.

### ✅ Level 16 – Admin Analytics
All 12 platform-wide metrics and reports — totals across restaurants,
customers, orders, revenue, refunds, active delivery partners, top
restaurants, top food items, most popular cuisine, daily orders, monthly
revenue, cancellation rate.

### ✅ Level 17 – Security & Data Integrity
JWT, role-based authorization, CORS, rate limiting on auth endpoints, global
exception handling, foreign key + unique constraints throughout, soft delete
on menu items, and a real audit log covering every service.

### ✅ Level 18 – Clean Architecture
A full `repositories/` layer built in from day one — every service goes
through a dedicated repository for database access, never querying the
database directly in a route or service.

### ✅ Level 19 – Database & Performance
Indexing, `joinedload` used throughout to avoid N+1 queries (including a
real fix applied to `get_current_user` itself, eagerly loading both the
Customer and Delivery Partner profile relationships in one query, since
every authenticated request passes through this one function).

### Bonus Features
- ✅ Redis caching (Restaurant)
- ✅ Docker & Docker Compose
- ✅ Real-time order tracking via WebSocket — genuinely broadcasting two kinds of live data: order status changes, and the delivery partner's live location while actively delivering
- ✅ Location integration — real geocoding via OpenStreetMap Nominatim (free, no API key or billing account needed), with straight-line distance calculated locally via the Haversine formula, chosen deliberately over Google Maps to avoid any billing risk
- ✅ PDF invoice generation, attached to the order confirmation email
- ✅ Excel sales reports (2 admin reports exportable)
- ✅ Celery background workers for every notification — no scheduled beat job, since nothing in this platform's requirements needs a recurring, clock-triggered check (every notification here fires from a real action, not a timer)
- ✅ Pytest unit & integration tests (18 tests, genuinely written and run)
- ✅ API versioning (`/api/v1/`)
- ✅ CI/CD-ready project structure, with a working GitHub Actions pipeline

---

## Project Structure

```
app/
├── main.py                  # FastAPI app, routers, startup, exception handlers
├── database.py               # database engine/session
├── config.py                 # centralized environment variable settings
├── celery_app.py             # celery application + broker (no beat schedule)
├── tasks.py                  # all celery task functions
├── models/                   # 16 SQLAlchemy models
├── schemas/                  # Pydantic request/response schemas
├── repositories/              # database access layer, one per domain table
├── services/                  # business logic, calls repositories
├── routes/                    # FastAPI routers
│   └── websocket.py           # live order status + delivery location
├── auth/                      # current_user, permissions
└── utils/                     # hashing, jwt, pagination, redis_cache, email,
                                # pdf, rate_limit, google_maps (Nominatim + Haversine)

.github/
└── workflows/
    └── ci.yml                 # runs Pytest automatically on every push/PR

alembic/                       # database migrations
tests/
├── unit/
└── integration/
```

---

## Prerequisites

- Python 3.11 or later
- Redis (Docker: `docker run -d -p 6379:6379 --name redis-food-delivery redis`)
- SMTP account for real emails (Gmail + App Password works well)

---

## Setup Instructions

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd "Restaurant & Food Delivery Management System"

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt<4.1" python-dotenv redis celery alembic reportlab openpyxl python-multipart httpx pytest
```

> **Important:** if `bcrypt` installs as version 4.1 or later, password
> hashing will crash. The pin above (`bcrypt<4.1`) handles this.

### 3. Start Redis

```bash
docker run -d -p 6379:6379 --name redis-food-delivery redis
```

> **If you're also running another project's Docker stack** (this platform
> was built alongside a Property Management and an Insurance platform in the
> same environment), make sure only one Redis instance and one app instance
> are bound to the same host ports at a time. This project's own Docker
> Compose setup maps its app to host port 8000 and Redis to 6381 by default.

### 4. Create your `.env` file

```env
DATABASE_URL=sqlite:///./food_delivery_platform.db

SECRET_KEY=change-this-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=Admin@12345
DEFAULT_ADMIN_PHONE=9999999999

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60
```

> **No Google Maps API key needed anywhere in this project.** Location
> features use OpenStreetMap's free Nominatim service instead — genuinely no
> billing account or credential of any kind required.

### 5. Run database migrations

```bash
alembic init alembic
```

Edit `alembic/env.py` — right after `config = context.config`, add:

```python
import os
import sys
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.database import Base
from app.models import *  # imports and registers all 16 models

config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
target_metadata = Base.metadata
```

Make sure there is only **one** `target_metadata = ...` line in the whole
file — the default Alembic template also defines `target_metadata = None`
further down, which silently overwrites the real one if both exist.

Clear `sqlalchemy.url` in `alembic.ini` (leave it blank), then:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 6. Start both processes — separate terminals

**Terminal 1 — the API server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 — the Celery worker (sends every email):**
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

> **No Celery Beat process is needed for this project** — unlike some
> others, there's no recurring, clock-triggered job here at all. Every
> notification fires as a direct result of a real action.

> **Windows-specific note:** the `--pool=solo` flag is required on the
> worker — Celery's default multi-process mode is unreliable on Windows.

### 7. Verify it's running

Open `http://localhost:8000/docs`. A default Admin is created automatically
— log in with the `DEFAULT_ADMIN_*` credentials from your `.env`.

---

## Running with Docker

```bash
docker-compose up --build
```

Then, in a new terminal, run migrations inside the running app container:
```bash
docker exec -it food-delivery-app alembic upgrade head
docker-compose restart app
```

---

## CI/CD

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the full Pytest
suite automatically on every push or Pull Request targeting `master` or
`dev`, spinning up a real Redis service container to match production
conditions. Recommended branch strategy:

```
master   ← protected, only receives merges via reviewed PR with passing CI
  └── dev   ← integration branch
        └── feature/* and fix/* branches
```


## Real Bugs Found and Fixed During Development

Worth documenting honestly, since these were caught by actually running the
app and carefully re-verifying, not just writing the code once and assuming
it was correct:

1. **`get_current_user` triggered a lazy-load query every time a service
   accessed `current_user.customer` or `current_user.delivery_partner`** —
   fixed by eagerly loading both relationships directly in the one function
   every authenticated request passes through, rather than fixing it
   separately in each service that needed it.
2. **A delivery partner could go `OFFLINE` while genuinely mid-delivery** —
   the original check only blocked switching back to `AVAILABLE`, missing
   the equally real case of going offline entirely. Fixed by blocking *any*
   manual status change while `ON_DELIVERY`.
3. **Coupon date validation crashed with "can't compare offset-naive and
   offset-aware datetimes"** — caused by SQLite not reliably preserving
   timezone information on `DateTime(timezone=True)` columns. Fixed by
   explicitly attaching UTC to the stored dates before comparing them
   against the current time.
4. **A route-ordering bug in the customer routes file** — `GET
   /customers/{customer_id}` was matching before `GET
   /customers/addresses`, causing FastAPI to try parsing "addresses" as an
   integer ID and fail. Fixed by placing the more specific address routes
   before the generic `/{customer_id}` routes.
5. **CI failed with `ModuleNotFoundError: No module named 'app'`** — caused
   by `pytest.ini` never having been created in the first place, so GitHub
   Actions' fresh checkout had no `pythonpath` configuration telling Pytest
   where to find the `app` package. Fixed by creating `pytest.ini` and
   additionally setting `PYTHONPATH` directly in the CI workflow as a second,
   independent safety net.

---

