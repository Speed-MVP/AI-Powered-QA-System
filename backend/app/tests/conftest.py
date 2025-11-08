import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.routes.auth import create_access_token
from app.models.user import User, UserRole
from app.models.company import Company
import uuid


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_company(db):
    """Create test company"""
    company = Company(
        id=str(uuid.uuid4()),
        company_name="Test Company",
        industry="Technology"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def test_user(db, test_company):
    """Create test user"""
    from app.routes.auth import get_password_hash
    user = User(
        id=str(uuid.uuid4()),
        company_id=test_company.id,
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        full_name="Test User",
        role=UserRole.admin,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_token(test_user):
    """Generate test JWT token"""
    return create_access_token(data={"sub": test_user.id})

