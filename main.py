from typing import List
from fastapi import FastAPI
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