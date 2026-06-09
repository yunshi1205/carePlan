# Care Plan Generator

Minimal Django app: web form → sync API → Anthropic Claude → care plan text.

See [design_doc.md](./design_doc.md) for full product design.

## Run with Docker

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

docker compose up --build
```

Open **http://localhost:8000** — fill the form and click **Generate care plan**. The API returns immediately with `careplan_id`; LLM runs later via queue (worker not implemented yet).

### Verify Redis queue (optional)

After submitting a form:

```bash
docker compose exec redis redis-cli LRANGE careplan:queue 0 -1
```

You should see the numeric `careplan_id` at the head of the list.

### Debug: trace order flow

| Where | What to look for |
| --- | --- |
| **Browser** | DevTools → Console, filter `ORDER_FLOW` — steps **F1–F7** |
| **Backend** | `docker compose logs -f web` — steps **B1–B6**, **S1–S2**, **L1–L2** |

Pause like a breakpoint:

- **Frontend:** in console run `ORDER_FLOW_BREAK = true`, then submit (hits `debugger` at each F-step).
- **Backend:** in `.env` or `docker-compose.yml` set `ORDER_FLOW_BREAKPOINT=1`, restart (hits `breakpoint()` at B1, B4, B6, S1, L1).

## API

**POST `/api/orders/`** — create order, save pending CarePlan, enqueue `careplan_id`, return immediately.

Response (`202`):

```json
{
  "message": "已收到",
  "careplan_id": 6,
  "order_id": "uuid-...",
  "status": "pending"
}
```

Poll **`GET /api/orders/<order_id>/`** later for status / care plan (when worker exists).

**GET `/api/orders/<id>/`** — fetch order by id (stored in PostgreSQL).

**GET `/api/orders/search/?q=...`** — search orders by name, medication, diagnosis, or id (`q` optional; empty lists all).

**GET `/api/orders/<id>/download/`** — download care plan as `.txt` (only when `status` is `completed`).

## PostgreSQL + mock data

`docker compose up` starts **PostgreSQL** and the web app. On first boot it runs migrations and loads mock data (`seed_mock_data`).

### TablePlus / DBeaver connection

| Field | Value |
| --- | --- |
| Host | `localhost` |
| Port | `5432` |
| Database | `careplan` |
| User | `careplan` |
| Password | `careplan` |

Tables: `patient`, `provider`, `"order"`, `careplan` (Django quotes `order` because it is a SQL keyword).

Mock seed includes 4 patients, 2 providers, 5 orders with care plans in various statuses (`completed`, `processing`, `failed`, `pending`).

Re-seed manually (only if DB is empty):

```bash
docker compose exec web python manage.py seed_mock_data
```

## Run locally (no Docker)

Requires PostgreSQL running (or only `docker compose up db`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set ANTHROPIC_API_KEY + POSTGRES_* 
python manage.py migrate
python manage.py seed_mock_data
python manage.py runserver
```

## Stack

- Python 3.12, Django 5
- PostgreSQL 16 + Redis 7 (Docker)
- Anthropic Messages API (Claude)
- No queues, workers, or WebSockets
