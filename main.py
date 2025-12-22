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

@app.post("/polls/{poll_id}/vote/{option_id}")
def vote(poll_id: int, option_id: int):
    db = SessionLocal()
    option = db.query(Option).filter_by(id=option_id, poll_id=poll_id).first()
    if not option:
        db.close()
        return {"error": "Option not found"}
    option.votes +=1
    db.commit()
    db.close()
    return {"message": "Vote recorded"}

@app.get("/polls/{poll_id}")
def get_results(poll_id: int):
    db = SessionLocal()
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        db.close()
        return {"error": "Poll not found"}
    result = {
        "question": poll.question,
        "results": [{"option": o.text, "votes": o.votes} for o in poll.options]
    }
    db.close()
    return result

class OptionAdd(BaseModel):
    text: str

@app.post("/polls/{poll_id}/options")
def add_option(poll_id: int, option: OptionAdd):
    db = SessionLocal()
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        db.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    new_option = Option(text=option.text,poll_id=poll_id)
    db.add(new_option)
    db.commit()
    db.refresh(new_option)
    db.close()
    return {"message": "Option added", "option_id": new_option.id}

class PollUpdate(BaseModel):
    question: str

@app.put("/polls/{poll_id}")
def update_poll(poll_id: int, poll_update: PollUpdate):
    db = SessionLocal()
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        db.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    poll.question = poll_update.question
    db.commit()
    updated_question = poll.question
    db.close()
    return {"message": "Poll updates successfully", "updated_question": updated_question}

@app.delete("/polls/{poll_id}/options/{option_id}")
def delete_option(poll_id: int, option_id: int):
    db = SessionLocal()
    option = db.query(Option).filter_by(id=option_id,poll_id=poll_id).first()
    if not option:
        db.close()
        raise HTTPException(status_code=404, detail="Option not found")
    db.delete(option)
    db.commit()
    db.close()
    return {"message": "Option deleted", "deleted_text": option.text}

@app.get("/polls/{poll_id}/stats")
def get_poll_stats(poll_id: int):
    with SessionLocal() as db:
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        total_votes = sum(option.votes for option in poll.options)
        options_stats = []
        for option in poll.options:
            percentage = (option.votes / total_votes * 100) if total_votes > 0 else 0
            options_stats.append({
                "id": option.id,
                "text": option.text,
                "votes": option.votes,
                "percentage": round(percentage,2)
            })
        most_voted = None
        if poll.options:
            most_voted_option = max(poll.options, key=lambda x: x.votes)
            most_voted = {
                "id": most_voted_option.id,
                "text": most_voted_option.text,
                "votes": most_voted_option.votes
            }
        stats = {
            "poll_id": poll_id,
            "question": poll.question,
            "total_votes": total_votes,
            "options_count": len(poll.options),
            "most_voted": most_voted,
            "options": options_stats
        }
        return stats