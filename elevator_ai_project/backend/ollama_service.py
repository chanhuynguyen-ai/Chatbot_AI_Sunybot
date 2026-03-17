import os
from typing import List, Optional

import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b-instruct")

FALLBACK_TEXT = "Sunybot hiện không thể trả lời câu hỏi này một cách đáng tin cậy."


class OllamaService:
    def _build_prompt(self, user_text: str, context_blocks: Optional[List[str]] = None, memory_summary: str = "") -> str:
        context_blocks = context_blocks or []
        context_text = "\n".join([f"- {item}" for item in context_blocks if item])
        return (
            "Bạn là Sunybot, trợ lý AI cho phần mềm thang máy thông minh.\n"
            "Nguyên tắc: chỉ trả lời về thang máy, vận hành, bảo trì, an toàn, thông tin nội bộ liên quan.\n"
            "Nếu câu hỏi ngoài phạm vi thì lịch sự yêu cầu người dùng hỏi đúng trọng tâm.\n"
            "Nếu có dữ liệu ngữ cảnh thì ưu tiên bám sát dữ liệu đó, không bịa thêm.\n"
            f"Tóm tắt hội thoại gần đây: {memory_summary or 'chưa có'}\n"
            f"Dữ liệu tham chiếu:\n{context_text or '- không có dữ liệu KB'}\n"
            f"Câu hỏi người dùng: {user_text}\n"
            "Hãy trả lời bằng tiếng Việt, ngắn gọn nhưng rõ ý, tối đa 4 câu."
        )

    def generate(self, user_text: str, context_blocks: Optional[List[str]] = None, memory_summary: str = "", connect_timeout: int = 3, read_timeout: int = 45) -> str:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": LLM_MODEL,
            "prompt": self._build_prompt(user_text, context_blocks=context_blocks, memory_summary=memory_summary),
            "stream": False,
            "options": {
                "num_predict": 180,
                "num_ctx": 1536,
                "temperature": 0.2,
                "top_p": 0.85,
            },
        }
        try:
            response = requests.post(url, json=payload, timeout=(connect_timeout, read_timeout))
            if response.status_code != 200:
                return FALLBACK_TEXT
            data = response.json()
            answer = (data.get("response") or "").strip()
            if not answer:
                return FALLBACK_TEXT
            return " ".join(answer.split())
        except Exception as exc:
            print(f"[OLLAMA_ERR] {exc}")
            return FALLBACK_TEXT

    def chat(self, user_text: str, context_blocks: Optional[List[str]] = None, memory_summary: str = "", timeout_sec: int = 45) -> str:
        return self.generate(user_text=user_text, context_blocks=context_blocks, memory_summary=memory_summary, read_timeout=timeout_sec)

    def healthcheck(self) -> bool:
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False
