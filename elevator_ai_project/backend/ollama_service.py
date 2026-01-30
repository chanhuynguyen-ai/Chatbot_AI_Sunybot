# backend/ollama_service.py
import os
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:1.5b")

FALLBACK_TEXT = "Sunybot hien khong the tra loi cau hoi, vui long tra loi cau hoi lien quan"

class OllamaService:
    def chat(self, user_text: str, timeout_sec: int = 12) -> str:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": LLM_MODEL,
            "prompt": user_text,
            "stream": False
        }
        try:
            r = requests.post(url, json=payload, timeout=timeout_sec)
            r.raise_for_status()
            data = r.json()
            ans = (data.get("response") or "").strip()
            return ans if ans else FALLBACK_TEXT
        except Exception:
            return FALLBACK_TEXT

