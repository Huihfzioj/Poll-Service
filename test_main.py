from fastapi.testclient import TestClient
from main import app, PollCreate, PollUpdate, OptionAdd
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import pytest
from database import Base, Poll, Option, SessionLocal

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    Base.metadate.create_all(bind=engine)
    db = TestingSessionLocal()

    poll1 = Poll(question="Test Poll 1")
    db.add(poll1)
    db.flush()
    poll1_options = [
        Option(text="Option A", poll_id=poll1.id),
        Option(text="Option B", poll_id=poll1.id),
        Option(text="Option C", poll_id=poll1.id)
    ]
    for opt in poll1_options:
        db.add(opt)

    poll2 = Poll(question="Test Poll 2")
    db.add(poll2)
    db.flush()
    
    poll2_options = [
        Option(text="Choice X", poll_id=poll2.id),
        Option(text="Choice Y", poll_id=poll2.id)
    ]
    for opt in poll2_options:
        db.add(opt)
    
    db.commit()
    db.close()
    yield  
    Base.metadata.drop_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
