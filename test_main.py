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


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[SessionLocal] = override_get_db()

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
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

def cleanup_test_database():
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

def test_vote():
    poll_response= client.get("/polls/1")
    previouspoll = poll_response.json()
    previousOption = next(opt for opt in previouspoll["results"] if opt["id"] == 1)
    response = client.post("/polls/1/vote/1")
    assert response.status_code == 200
    assert response.json()["message"] == "Vote recorded"
    poll_response = client.get("/polls/1")
    poll_data = poll_response.json()
    option_1 = next(opt for opt in poll_data["results"] if opt["id"] == 1)
    assert option_1["votes"] == previousOption["votes"]+1

def test_vote_invalid_option():
    response = client.post("/polls/1/vote/999")
    assert response.status_code == 404

def test_add_option():
    new_option = {"text": "New Option"}
    
    response = client.post("/polls/1/options", json=new_option)
    assert response.status_code == 200
    data = response.json()
    assert "option_id" in data
    assert "message" in data
    poll_response = client.get("/polls/1")
    poll_data = poll_response.json()
    options = [opt["option"] for opt in poll_data["results"]]
    assert new_option["text"] in options

def test_add_option_to_nonexistent_poll():
    response = client.post("/polls/999/options", json={"text": "Test"})
    assert response.status_code == 404

def test_update_poll():
    update_data = {"question": "UPDATED: New Question Text"}
    
    response = client.put("/polls/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Poll updated successfully"
    assert data["updated_question"] == update_data["question"]

    poll_response = client.get("/polls/1")
    assert poll_response.json()["question"] == update_data["question"]

def test_update_nonexistent_poll():
    response = client.put("/polls/999", json={"question": "Test"})
    assert response.status_code == 404

def test_delete_option():
    add_response = client.post("/polls/1/options", json={"text": "Option to Delete"})
    option_id = add_response.json()["option_id"]
    response = client.delete(f"/polls/1/options/{option_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Option deleted"
    assert data["deleted_text"] == "Option to Delete"

    poll_response = client.get("/polls/1")
    poll_data = poll_response.json()
    option_ids = [opt["id"] for opt in poll_data["results"]]
    assert option_id not in option_ids

def test_delete_nonexistent_option():
    response = client.delete("/polls/1/options/999")
    assert response.status_code == 404

def test_delete_poll():
    poll_data = {
        "question": "Poll to be deleted",
        "options": ["A", "B"]
    }
    create_response = client.post("/polls", json=poll_data)
    poll_id = create_response.json()["poll_id"]
    response = client.delete(f"/polls/{poll_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == f"Poll {poll_id} deleted successfully"
    assert data["deleted_poll"]["id"] == poll_id

    get_response = client.get(f"/polls/{poll_id}")
    assert get_response.status_code == 404

def test_delete_nonexistent_poll():
    response = client.delete("/polls/99999")
    assert response.status_code == 404

def test_get_poll_stats():
    poll_data = {
        "question": "What is your favorite color?",
        "options": ["Red", "Blue", "Green", "Yellow"]
    }
    response = client.post("/polls", json=poll_data)
    data = response.json()
    poll_id = data["poll_id"]
    prevOptions = client.get(f"/polls/{poll_id}").json()["results"]
    client.post(f"/polls/{poll_id}/vote/{prevOptions[0]["id"]}")
    client.post(f"/polls/{poll_id}/vote/{prevOptions[0]["id"]}")
    client.post(f"/polls/{poll_id}/vote/{prevOptions[1]["id"]}")
    client.post(f"/polls/{poll_id}/vote/{prevOptions[2]["id"]}")
    response = client.get(f"/polls/{poll_id}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "poll_id" in data
    assert "question" in data
    assert "total_votes" in data
    assert "options_count" in data
    assert "most_voted" in data
    assert "options" in data
    
    assert data["total_votes"] == 4
    assert data["options_count"] == 4

    for option in data["options"]:
        assert "percentage" in option
        assert 0 <= option["percentage"] <= 100

def run_all_tests():
    tests = [
        test_health,
        test_create_poll,
        test_create_poll_invalid,
        test_get_poll,
        test_get_nonexistent_poll,
        test_vote,
        test_vote_invalid_option,
        test_add_option,
        test_add_option_to_nonexistent_poll,
        test_update_poll,
        test_update_nonexistent_poll,
        test_delete_option,
        test_delete_nonexistent_option,
        test_delete_poll,
        test_delete_nonexistent_poll,
        test_get_poll_stats
    ]
    passed,failed=0,0
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"{test_func.__name__} FAILED: {str(e)}\n")
        except Exception as e:
            failed += 1
            print(f"{test_func.__name__} ERROR: {str(e)}\n")
        finally :
            cleanup_test_database()
    print("=" * 20)
    print(f" TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 20) 

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)