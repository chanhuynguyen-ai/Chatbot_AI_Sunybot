from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time

from backend.chatbot_engine import ChatbotEngine

# =========================
# App & Engine
# =========================
app = FastAPI(title="Sunybot Elevator Chatbot", version="1.0.0")
engine = ChatbotEngine()

# =========================
# Path config
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "gui", "web")
PAGES_DIR = os.path.join(WEB_DIR, "pages")
STATIC_DIR = os.path.join(WEB_DIR, "static")
FAVICON_PATH = os.path.join(STATIC_DIR, "favicon.ico")

# =========================
# Static files
# =========================
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# =========================
# Favicon
# =========================
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if os.path.isfile(FAVICON_PATH):
        return FileResponse(FAVICON_PATH)
    return Response(status_code=204)

# =========================
# UI Routes
# =========================
@app.get("/")
def home():
    """Home screen"""
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.get("/pages/{page}")
def serve_pages(page: str):
    """
    Serve UI pages:
    /pages/call.html
    /pages/assistant.html
    /pages/guide.html
    /pages/sos.html
    /pages/maintenance.html
    """
    safe_page = os.path.basename(page)  # chống ../
    file_path = os.path.join(PAGES_DIR, safe_page)

    if not os.path.isfile(file_path):
        return JSONResponse(
            status_code=404,
            content={"error": "Page not found"}
        )

    return FileResponse(file_path)

# =========================
# Healthcheck
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# =========================
# Elevator Status (PHASE 1 - MOCK)
# =========================
@app.get("/api/elevator/status")
def elevator_status():
    """
    Mock realtime status.
    PHASE 2+ sẽ thay bằng dữ liệu thật (PLC/CV)
    """
    return {
        "elevator_id": 1,
        "floor": 5,
        "direction": "UP",          # UP / DOWN / IDLE
        "door": "CLOSED",           # OPEN / CLOSED / JAM
        "people_count": 4,
        "overload": False,
        "status": "NORMAL",         # NORMAL / WARNING / ERROR
        "time": time.strftime("%H:%M:%S")
    }

# =========================
# Chatbot API
# =========================
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    source: str
    intent: Optional[str] = None
    confidence: Optional[float] = None

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    r = engine.handle(req.message)
    return {
        "answer": r.get("answer", ""),
        "source": r.get("source", "UNKNOWN"),
        "intent": r.get("intent"),
        "confidence": r.get("confidence"),
    }

