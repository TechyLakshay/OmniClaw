
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from agents.orchestrator import run_orchestrator
from memory.database import save_message, load_history
from core.email_processor import process_latest_unread_email
import logging
import uuid
import os
import time
from dotenv import load_dotenv

load_dotenv()
#logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s   - %(levelname)s   - %(message)s'
)

logger = logging.getLogger(__name__)
#fastapi
app = FastAPI()

#RATE LIMITING
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))
USER_REQUESTS: dict[str, list[float]] = {}

#Request model
class ChatRequest(BaseModel):
    user_id: str
    message: str


class ProcessLatestEmailRequest(BaseModel):
    mark_as_read: bool = False


def validate_request(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long")

def authenticate(api_key: str):
    if api_key != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorised")

# Rate Limiting - Sliding Window Algorithm
def enforce_rate_limit(user_id: str):
    now = time.time()
    recent_requests = USER_REQUESTS.get(user_id, [])
    recent_requests = [
        request_time
        for request_time in recent_requests
        if now - request_time < RATE_LIMIT_WINDOW_SECONDS
    ]

    if len(recent_requests) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX_REQUESTS} requests in {RATE_LIMIT_WINDOW_SECONDS} seconds.",
        )

    recent_requests.append(now)
    USER_REQUESTS[user_id] = recent_requests

@app.get("/health")
async def health():
    return {"status": "Fine"}   

@app.post("/chat")
async def chat(req: ChatRequest, x_api_key: str = Header(...)):
    request_id = str(uuid.uuid4())
    logger.info(f"request_id={request_id} user={req.user_id} msg_len={len(req.message)}")

    try:
        authenticate(x_api_key)
        validate_request(req)
        enforce_rate_limit(req.user_id)

        history = load_history(req.user_id)
        logger.info(f"request_id={request_id} history_loaded={len(history)} messages")

        response = run_orchestrator(req.message, history)

        save_message(req.user_id, "human", req.message)
        save_message(req.user_id, "ai", response)
        logger.info(f"request_id={request_id} status=success")

        return {
            "request_id": request_id,
            "response": response
        }

    except HTTPException as e:
        logger.warning(f"request_id={request_id} status=rejected detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"request_id={request_id} status=error error={str(e)}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/process-latest-email")
async def process_latest_email(req: ProcessLatestEmailRequest, x_api_key: str = Header(...)):
    request_id = str(uuid.uuid4())
    logger.info(f"request_id={request_id} action=process_latest_email")

    try:
        authenticate(x_api_key)
        result = process_latest_unread_email(mark_as_read=req.mark_as_read)
        logger.info(f"request_id={request_id} status={result.get('status')}")
        return {
            "request_id": request_id,
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"request_id={request_id} status=error error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
