import logging
import pytest
import uuid
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import ARRAY
from sqlalchemy.ext.compiler import compiles
from fastapi import Header

from app.main import app
from app.db.base import Base
from app.api.deps import get_db, get_current_auth
from app.core.errors import UnauthorizedError
from app.core.security import AuthClaims



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_workspace_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_headers(mock_user_id):
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest.fixture
async def client(db_session, mock_user_id):
    async def override_get_db():
        yield db_session

    async def override_get_current_auth(authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid authorization header")
        token = authorization.split(" ", 1)[1]
        
        # Parse token as user_id:email for dynamic mocking, default to mock_user_id for test-token
        if token == "test-token":
            return AuthClaims(user_id=uuid.UUID(mock_user_id), email="test@example.com")
        elif ":" in token:
            uid, email = token.split(":", 1)
            # Create a deterministic UUID from the uid string if it's not a valid UUID format
            import hashlib
            uid_uuid = uuid.UUID(hashlib.md5(uid.encode()).hexdigest())
            return AuthClaims(user_id=uid_uuid, email=email)
            
        raise UnauthorizedError("Invalid or expired token")
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_auth] = override_get_current_auth
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
