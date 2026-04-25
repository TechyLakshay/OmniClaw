
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

#MCP Middleware for LOGGING and ERROR HANDLING
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log each request once and attach a request id for the response."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # The request id is stored on the request so route handlers can reuse it.
    request.state.request_id = request_id

    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        "request_id=%s method=%s path=%s status=%s duration=%.2fs",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return one JSON error response for unhandled server errors."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "request_id": request_id,
                "detail": exc.detail,
            },
        )

    logger.error("request_id=%s status=error error=%s", request_id, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "request_id": request_id,
            "detail": "Internal error",
        },
    )

@app.get("/health")
async def health():
    return {"status": "Fine"}   

@app.post("/chat")
async def chat(req: ChatRequest, request: Request, x_api_key: str = Header(...)):
    authenticate(x_api_key)
    validate_request(req)
    enforce_rate_limit(req.user_id)

    history = load_history(req.user_id)
    response = run_orchestrator(req.message, history)

    save_message(req.user_id, "human", req.message)
    save_message(req.user_id, "ai", response)

    return {
        "request_id": request.state.request_id,
        "response": response
    }


@app.post("/process-latest-email")
async def process_latest_email(req: ProcessLatestEmailRequest, request: Request, x_api_key: str = Header(...)):
    authenticate(x_api_key)
    result = process_latest_unread_email(mark_as_read=req.mark_as_read)

    return {
        "request_id": request.state.request_id,
        **result,
    }
