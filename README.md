# Care Plan Generator

Minimal Django app: web form → sync API → Anthropic Claude → care plan text.

See [design_doc.md](./design_doc.md) for full product design.

## Run with Docker

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

docker compose up --build
```

Open **http://localhost:8000** — submit the form; API returns immediately. **Celery worker** generates the care plan in the background. The frontend does **not** auto-update — refresh Search or check TablePlus manually.

### Verify Celery worker

```bash
# 1. Start everything (web + worker + db + redis)
docker compose up --build

# 2. Watch worker logs in another terminal
docker compose logs -f worker

# 3. Submit a form at http://localhost:8000 — worker should log:
#    [CELERY] Task started careplan_id=...
#    [ORDER_FLOW L1] llm.generate_care_plan ...
#    [CELERY] Task completed careplan_id=...

# 4. Check DB status (TablePlus or psql)
docker compose exec db psql -U careplan -d careplan -c \
  "SELECT id, status, LEFT(content, 40) FROM careplan ORDER BY id DESC LIMIT 5;"

# 5. Manual API check (use order_id from submit response)
curl -s http://localhost:8000/api/orders/<order_id>/ | python3 -m json.tool
```

Worker consumes tasks from **Redis via Celery broker** (`redis://redis:6379/0`), not the old manual `careplan:queue` list.

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

Poll **`GET /api/orders/<order_id>/`** manually when you want to see if generation finished (no auto frontend update).

## Celery worker

| Component | Role |
| --- | --- |
| `care/tasks.py` | `generate_care_plan_task` — LLM + DB update, max 3 attempts |
| `worker` service | `celery -A config worker -Q careplan` |
| Redis | Celery broker (task queue) |

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
- PostgreSQL 16 + Redis 7 + Celery worker (Docker)
- Anthropic Messages API (Claude)
