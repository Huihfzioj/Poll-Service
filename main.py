from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import Option, Poll, SessionLocal

app = FastAPI(title="Poll Service")

@app.get("/health")
def health():
    return {"status": "ok"}

class PollCreate(BaseModel):
    question: str
    options: List[str]

@app.post("/polls")
def create_poll(poll: PollCreate):
    db = SessionLocal()
    new_poll = Poll(question = poll.question)
    db.add(new_poll)
    db.commit()
    db.refresh(new_poll)
    for option in poll.options:
        db.add(Option(text=option, poll_id=new_poll.id))
    db.commit()
    db.refresh(new_poll)
    db.close()
    return {"poll_id": new_poll.id}


@app.delete("/polls/{poll_id}")
def delete_poll(poll_id: int):
    db = SessionLocal()
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll Not Found")
    try :
        db.delete(poll)
        db.commit()
        return {
            "message": f"Poll {poll_id} deleted successfully",
            "deleted_poll": {
                "id": poll_id,
                "question": poll.question
            }
        }
    except Exception as e :
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting poll: {str(e)}")
    finally :
        db.close()