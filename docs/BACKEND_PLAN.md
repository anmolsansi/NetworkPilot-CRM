# Backend Plan

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic v2
- pytest + pytest-asyncio

## Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # Dependencies
│   │   ├── router.py        # Route registration
│   │   └── routes/
│   │       ├── health.py
│   │       ├── me.py
│   │       ├── workspaces.py
│   │       ├── people.py
│   │       ├── activities.py
│   │       ├── dashboard.py
│   │       ├── templates.py
│   │       ├── calendar.py
│   │       └── extension.py
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── security.py      # JWT verification
│   │   ├── errors.py        # Custom exceptions
│   │   └── logging.py       # Structured logging
│   ├── db/
│   │   ├── session.py       # DB session
│   │   ├── base.py          # Model base
│   │   └── migrations/      # Alembic
│   ├── models/
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── person.py
│   │   ├── activity.py
│   │   ├── template.py
│   │   └── settings.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── users.py
│   │   ├── workspaces.py
│   │   ├── people.py
│   │   ├── activities.py
│   │   ├── dashboard.py
│   │   ├── templates.py
│   │   ├── calendar.py
│   │   └── extension.py
│   ├── services/
│   │   ├── user_service.py
│   │   ├── workspace_service.py
│   │   ├── people_service.py
│   │   ├── activity_service.py
│   │   ├── transition_service.py
│   │   ├── dashboard_service.py
│   │   ├── template_service.py
│   │   ├── calendar_link_service.py
│   │   └── url_normalizer.py
│   └── main.py
├── app/tests/
│   ├── unit/
│   └── integration/
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Key Patterns

### Dependencies
```python
def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    # Verify JWT, extract user_id, bootstrap user
```

### Service Pattern
```python
class PeopleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, workspace_id: UUID, data: PersonCreate) -> Person:
        # Normalize URL, check duplicates, create
```

### Error Handling
```python
class AppError(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details
```

## Stage Transition Rules

The `TransitionService` centralizes all stage changes:

| Action | New Stage | Next Action | Due Date |
|--------|-----------|-------------|----------|
| invite_sent | invite_pending | acceptance_check | +default_acceptance_check_delay_days |
| accepted | accepted | send_first_message | today |
| message_sent | waiting_for_reply | follow_up_1 | +default_follow_up_delay_days |
| follow_up_1_sent | follow_up_1_sent | follow_up_2 | +default_follow_up_delay_days |
| reply_received | replied | none | null |

## Testing

- Unit tests: URL normalizer, transitions, calendar link, templates
- Integration tests: Full API flows against test DB
- Run: `pytest` from backend directory
