# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests — Configuración y Fixtures Compartidas
# ═══════════════════════════════════════════════════════════

import pytest
import os
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, SessionLocal, UserDB
from security import hash_password, create_access_token
from config import settings
from deps import get_db


@pytest.fixture(scope="session")
def db_engine():
    """Motor de BD para tests (SQLite en memoria)"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Sesión de BD para cada test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    # Seed data inicial
    session.add(UserDB(
        id="admin-id",
        username="admin",
        password=hash_password("admin123"),
        name="Administrador",
        email="admin@emantix.com",
        role="admin",
        active=True
    ))
    session.add(UserDB(
        id="tecnico-id",
        username="tecnico",
        password=hash_password("tecnico123"),
        name="Técnico",
        email="tecnico@emantix.com",
        role="tecnico",
        active=True
    ))
    session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db_session):
    """Override get_db para tests"""
    def _get_db():
        return db_session
    
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """Cliente de prueba FastAPI"""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Token JWT para admin"""
    return create_access_token(data={
        "sub": "admin-id",
        "username": "admin",
        "role": "admin",
        "name": "Administrador"
    })


@pytest.fixture
def tecnico_token():
    """Token JWT para técnico"""
    return create_access_token(data={
        "sub": "tecnico-id",
        "username": "tecnico",
        "role": "tecnico",
        "name": "Técnico"
    })


@pytest.fixture
def invalid_token():
    """Token JWT inválido"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"


@pytest.fixture
def expired_token():
    """Token JWT expirado"""
    payload = {
        "sub": "admin-id",
        "username": "admin",
        "role": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc)
    }
    import jwt
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


@pytest.fixture
def admin_headers(admin_token):
    """Headers con token admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def tecnico_headers(tecnico_token):
    """Headers con token técnico"""
    return {"Authorization": f"Bearer {tecnico_token}"}


@pytest.fixture
def invalid_headers(invalid_token):
    """Headers con token inválido"""
    return {"Authorization": f"Bearer {invalid_token}"}


@pytest.fixture
def expired_headers(expired_token):
    """Headers con token expirado"""
    return {"Authorization": f"Bearer {expired_token}"}


@pytest.fixture
def create_test_user(db_session):
    """Factory para crear usuarios de prueba"""
    def _create_user(username: str, password: str = "test123", role: str = "tecnico", active: bool = True):
        import uuid
        user = UserDB(
            id=str(uuid.uuid4()),
            username=username.lower(),
            password=hash_password(password),
            name=f"Test {username}",
            email=f"{username}@test.com",
            role=role,
            active=active
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    return _create_user
