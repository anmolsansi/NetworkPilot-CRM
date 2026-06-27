# Backend

FastAPI + SQLAlchemy + Alembic API for NetworkPilot CRM.

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```
