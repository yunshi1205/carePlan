# Care Plan Generator

Minimal Django app: web form → sync API → Anthropic Claude → care plan text.

See [design_doc.md](./design_doc.md) for full product design.

## Run with Docker

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

docker compose up --build
```

Open **http://localhost:8000** — fill the form and click **Generate care plan**. The page waits until the API finishes (sync).

## API

**POST `/api/orders/`** — create order and generate care plan in one request.

Request body (JSON):

```json
{
  "patient_first_name": "A.",
  "patient_last_name": "B.",
  "medication_name": "IVIG",
  "primary_diagnosis": "Myasthenia gravis",
  "patient_records": "Clinical notes..."
}
```

Response statuses: `pending` → `processing` → `completed` | `failed`

- `care_plan` is included only when `status` is `completed`
- `error` is included only when `status` is `failed`

**GET `/api/orders/<id>/`** — fetch order by id (in-memory; lost on restart).

**GET `/api/orders/search/?q=...`** — search orders by name, medication, diagnosis, or id (`q` optional; empty lists all).

**GET `/api/orders/<id>/download/`** — download care plan as `.txt` (only when `status` is `completed`).

## Run locally (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-20250514
python manage.py runserver
```

## Stack

- Python 3.12, Django 5
- In-memory order store (no database)
- Anthropic Messages API (Claude)
- No queues, workers, or WebSockets
