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

def test_create_poll():
    poll_data = {
        "question": "What is your favorite color?",
        "options": ["Red", "Blue", "Green", "Yellow"]
    }
    response = client.post("/polls", json=poll_data)
    assert response.status_code == 200
    data = response.json()
    assert "poll_id" in data
    assert isinstance(data["poll_id"], int)
    return data['poll_id']

def test_create_poll_invalid():

    response = client.post("/polls", json={"options": ["A", "B"]})
    assert response.status_code == 422

    response = client.post("/polls", json={"question": "Test"})
    assert response.status_code == 422

    response = client.post("/polls", json={"question": "Test", "options": []})
    assert response.status_code == 422

def test_get_poll():

    poll_data = {
        "question": "Dynamic Test Poll",
        "options": ["Opt1", "Opt2"]
    }
    create_response = client.post("/polls", json=poll_data)
    poll_id = create_response.json()["poll_id"]
    response = client.get(f"/polls/{poll_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == poll_id
    assert data["question"] == poll_data["question"]
    assert len(data["results"]) == len(poll_data["options"])

def test_get_nonexistent_poll():
    response = client.get("/polls/99999")
    assert response.status_code == 404
    assert "detail" in response.json()