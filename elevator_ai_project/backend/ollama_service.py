# backend/ollama_service.py
import os
import time
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:1.5b")

FALLBACK_TEXT = "Sunybot hiện không thể trả lời câu hỏi này, vui lòng nhập câu hỏi khác"

class OllamaService:
    def generate(self, prompt: str, connect_timeout: int = 3, read_timeout: int = 120, retries: int = 1) -> str:
        """
        connect_timeout: thời gian bắt tay TCP (nên ngắn)
        read_timeout: thời gian chờ model trả xong (nên dài)
        """
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            # Tuỳ chọn để nhanh hơn (bạn có thể bỏ):
            "options": {
                "num_predict": 256,     # giới hạn số token sinh ra
                "temperature": 0.7
            }
        }

        last_err = None
        for attempt in range(retries + 1):
            try:
                r = requests.post(url, json=payload, timeout=(connect_timeout, read_timeout))
                # nếu ollama trả lỗi JSON kiểu {"error": "..."}
                if r.status_code != 200:
                    last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                    time.sleep(0.5)
                    continue

                data = r.json()
                if "error" in data:
                    last_err = f"Ollama error: {data.get('error')}"
                    time.sleep(0.5)
                    continue

                ans = (data.get("response") or "").strip()
                if ans:
                    return ans

                last_err = "Empty response"
                time.sleep(0.5)

            except Exception as e:
                last_err = repr(e)
                time.sleep(0.5)

        # In ra warning để bạn nhìn log terminal biết lỗi thật
        print(f"[OLLAMA_WARN] generate failed: {last_err}")
        return FALLBACK_TEXT

    # giữ tương thích nếu engine đang gọi .chat()
    def chat(self, user_text: str, timeout_sec: int = 120) -> str:
        # Bạn muốn giảm ràng buộc: OK — gửi thẳng user_text cho model
        return self.generate(user_text, read_timeout=timeout_sec, retries=1)

