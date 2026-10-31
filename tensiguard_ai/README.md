# TensiGuard DZ AI

FastAPI and SQLAlchemy decision-support service for hypertension monitoring. It is educational only, does not diagnose disease, and does not recommend medication changes.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python ..\ai.py
```

API docs: http://localhost:8000/docs

SQLite is the default. PostgreSQL: set `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/tensiguard`.

## API examples

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/patients -ContentType 'application/json' -Body '{"full_name":"Ahmed Benali","age":67,"sex":"male","weight_kg":78,"height_cm":172,"phone_number":"+213555010101","language":"fr"}'
Invoke-RestMethod http://localhost:8000/health
```

Create a reading:

```json
POST /patients/{id}/readings
{"systolic":118,"diastolic":78,"pulse":72,"source":"manual","symptoms":[]}
```

Docker:

```powershell
docker compose up --build
```

Medical limits in this service are general educational decision-support thresholds. A clinician must validate care decisions. Emergency symptoms immediately trigger urgent handling.
