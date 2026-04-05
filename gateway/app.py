
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from agents.orchestrator import run_orchestrator
from core.llm import invoke_llm
from memory.database import save_message, load_history
import logging
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

def validate_request(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long")

def authenticate(api_key: str):
    if api_key != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorised")

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