from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
import os

from backend.chatbot_engine import ChatbotEngine

app = FastAPI(title="Sunybot Elevator Chatbot", version="1.0.0")
engine = ChatbotEngine()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "gui", "web")
FAVICON_PATH = os.path.join(WEB_DIR, "static", "favicon.ico")
# nếu bạn có folder static (ảnh/css/js)
STATIC_DIR = os.path.join(WEB_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if os.path.isfile(FAVICON_PATH):
        return FileResponse(FAVICON_PATH)
    # Không có icon thì trả 204 để trình duyệt khỏi kêu 404/500
    return Response(status_code=204)


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    source: str
    intent: Optional[str] = None
    confidence: Optional[float] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    r = engine.handle(req.message)
    return {
        "answer": r.get("answer"),
        "source": r.get("source"),
        "intent": r.get("intent"),
        "confidence": r.get("confidence"),
    }

