from typing import List
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram
from pydantic import BaseModel
import logging
from database import Option, Poll, SessionLocal
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poll Service")

REQUEST_LATENCY = Histogram(
    "poll_service_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)
REQUEST_COUNT = Counter(
    "poll_service_request_count",
    "Total number of requests",
    ["method", "endpoint", "http_status"]
)
DB_OPERATIONS = Counter(
    "poll_service_db_operations_total",
    "Database operations count",
    ["operation"]
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time

    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    return response

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

class PollCreate(BaseModel):
    question: str
    options: List[str]

class OptionAdd(BaseModel):
    text: str

class PollUpdate(BaseModel):
    question: str

@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "ok"}

@app.post("/polls")
def create_poll(poll: PollCreate):
    logger.info(f"Creating poll with question: {poll.question}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="create_poll").inc()
        new_poll = Poll(question=poll.question)
        db.add(new_poll)
        db.commit()
        db.refresh(new_poll)
        
        for option in poll.options:
            DB_OPERATIONS.labels(operation="add_option").inc()
            db.add(Option(text=option, poll_id=new_poll.id))
        
        db.commit()
        db.refresh(new_poll)
        logger.info(f"Poll created with id: {new_poll.id}")
        return {"poll_id": new_poll.id}

@app.delete("/polls/{poll_id}")
def delete_poll(poll_id: int):
    logger.info(f"Deleting poll with id: {poll_id}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="delete_poll").inc()
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            logger.warning(f"Poll {poll_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Poll Not Found")
        try:
            deleted_question = poll.question
            db.delete(poll)
            db.commit()
            logger.info(f"Poll {poll_id} deleted successfully")
            return {
                "message": f"Poll {poll_id} deleted successfully",
                "deleted_poll": {"id": poll_id, "question": deleted_question}
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting poll {poll_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error deleting poll: {str(e)}")

@app.post("/polls/{poll_id}/vote/{option_id}")
def vote(poll_id: int, option_id: int):
    logger.info(f"Voting on poll {poll_id}, option {option_id}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="vote").inc()
        option = db.query(Option).filter_by(id=option_id, poll_id=poll_id).first()
        if not option:
            logger.warning(f"Option {option_id} not found in poll {poll_id}")
            raise HTTPException(status_code=404, detail="Option not found")
        option.votes += 1
        db.commit()
        logger.info(f"Vote recorded for option {option_id} in poll {poll_id}")
        return {"message": "Vote recorded"}

@app.get("/polls/{poll_id}")
def get_results(poll_id: int):
    logger.info(f"Fetching results for poll {poll_id}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="get_results").inc()
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            logger.warning(f"Poll {poll_id} not found for results")
            raise HTTPException(status_code=404, detail="Poll not found")
        result = {
            "id": poll.id,
            "question": poll.question,
            "results": [{"id": o.id, "option": o.text, "votes": o.votes} for o in poll.options]
        }
        logger.info(f"Results returned for poll {poll_id}")
        return result

@app.post("/polls/{poll_id}/options")
def add_option(poll_id: int, option: OptionAdd):
    logger.info(f"Adding option to poll {poll_id}: {option.text}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="add_option").inc()
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            logger.warning(f"Poll {poll_id} not found for adding option")
            raise HTTPException(status_code=404, detail="Poll not found")
        new_option = Option(text=option.text, poll_id=poll_id)
        db.add(new_option)
        db.commit()
        db.refresh(new_option)
        logger.info(f"Option added with id: {new_option.id}")
        return {"message": "Option added", "option_id": new_option.id}

@app.put("/polls/{poll_id}")
def update_poll(poll_id: int, poll_update: PollUpdate):
    logger.info(f"Updating poll {poll_id} with new question: {poll_update.question}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="update_poll").inc()
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            logger.warning(f"Poll {poll_id} not found for update")
            raise HTTPException(status_code=404, detail="Poll not found")
        poll.question = poll_update.question
        db.commit()
        logger.info(f"Poll {poll_id} updated successfully")
        return {
            "message": "Poll updated successfully",
            "updated_question": poll_update.question,
            "poll_id": poll_id
        }

@app.delete("/polls/{poll_id}/options/{option_id}")
def delete_option(poll_id: int, option_id: int):
    logger.info(f"Deleting option {option_id} from poll {poll_id}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="delete_option").inc()
        option = db.query(Option).filter_by(id=option_id, poll_id=poll_id).first()
        if not option:
            logger.warning(f"Option {option_id} not found in poll {poll_id} for deletion")
            raise HTTPException(status_code=404, detail="Option not found")
        deleted_text = option.text
        db.delete(option)
        db.commit()
        logger.info(f"Option {option_id} deleted successfully")
        return {
            "message": "Option deleted",
            "deleted_text": deleted_text,
            "poll_id": poll_id,
            "option_id": option_id
        }

@app.get("/polls/{poll_id}/stats")
def get_poll_stats(poll_id: int):
    logger.info(f"Fetching stats for poll {poll_id}")
    with SessionLocal() as db:
        DB_OPERATIONS.labels(operation="get_stats").inc()
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            logger.warning(f"Poll {poll_id} not found for stats")
            raise HTTPException(status_code=404, detail="Poll not found")
        total_votes = sum(option.votes for option in poll.options)
        options_stats = []
        for option in poll.options:
            percentage = (option.votes / total_votes * 100) if total_votes > 0 else 0
            options_stats.append({
                "id": option.id,
                "text": option.text,
                "votes": option.votes,
                "percentage": round(percentage, 2)
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
        logger.info(f"Stats computed for poll {poll_id}")
        return stats