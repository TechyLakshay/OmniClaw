from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
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

# Logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s   - %(levelname)s   - %(message)s'
)

logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI()

# Simple in-memory rate limiting
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))
USER_REQUESTS: dict[str, list[float]] = {}


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    user_id: str
    message: str


class ProcessLatestEmailRequest(BaseModel):
    """Request body for processing latest unread email."""

    mark_as_read: bool = False

# Request Validation
def validate_request(req: ChatRequest) -> None:
    """Validate chat input constraints."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long")

#Authentication
def authenticate(api_key: str) -> None:
    """Validate API key from request headers."""
    if api_key != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorised")

#Ratelimiting
def enforce_rate_limit(user_id: str) -> None:
    """Apply a sliding-window rate limit per user."""
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

#middleware - logs and error 
@app.middleware("http")
async def request_logging_and_error_middleware(request: Request, call_next):
    """Log request lifecycle and convert unhandled errors to JSON.

    Why this middleware helps:
    - One place for request timing and status logs
    - Consistent 500 response body for unexpected crashes
    - Easier debugging when a request fails before endpoint try/except blocks
    """

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    logger.info("request_id=%s method=%s path=%s started", request_id, request.method, request.url.path)

    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["x-request-id"] = request_id
        return response
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_id=%s method=%s path=%s status=500 elapsed_ms=%.2f error=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
            str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"request_id": request_id, "detail": "Internal error"},
        )

#fastapi endpoints
@app.get("/health")
async def health():
    return {"status": "Fine"}   

@app.post("/chat")
async def chat(req: ChatRequest, request: Request, x_api_key: str = Header(...)):
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        # Fallback if middleware is bypassed in tests.
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
async def process_latest_email(req: ProcessLatestEmailRequest, request: Request, x_api_key: str = Header(...)):
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
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
