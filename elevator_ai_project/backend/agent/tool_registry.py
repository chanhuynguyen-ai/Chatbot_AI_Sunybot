import time
import uuid
from typing import Any, Dict, List, Optional

from backend.embedding_service import EmbeddingService
from backend.employee_service import (
    find_employee_by_code,
    find_employee_by_name,
    format_employee_answer,
    is_employee_code,
)
from backend.ollama_service import FALLBACK_TEXT, OllamaService
from backend.semantic_matcher import SemanticMatcher


class ToolRegistry:
    def __init__(
        self,
        matcher: Optional[SemanticMatcher] = None,
        embedder: Optional[EmbeddingService] = None,
        ollama: Optional[OllamaService] = None,
    ):
        self.matcher = matcher or SemanticMatcher()
        self.matcher.load_from_db()
        self.embedder = embedder or EmbeddingService()
        self.ollama = ollama or OllamaService()

    def run(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        handler = getattr(self, f"tool_{tool_name}", None)
        if not handler:
            raise ValueError(f"Tool không tồn tại: {tool_name}")
        return handler(**(args or {}))

    def tool_employee_lookup(self, query: str) -> Dict[str, Any]:
        emp = None
        if is_employee_code(query):
            emp = find_employee_by_code(query)
        if not emp:
            emp = find_employee_by_name(query)
        if not emp:
            return {
                "ok": False,
                "source": "EMPLOYEE",
                "message": "Không tìm thấy nhân viên phù hợp.",
            }
        return {
            "ok": True,
            "source": "EMPLOYEE",
            "employee": emp,
            "message": format_employee_answer(emp),
        }

    def tool_kb_search(self, query: str, top_k: int = 3, threshold: float = 0.72) -> Dict[str, Any]:
        user_emb = self.embedder.embed(query, task="query")
        results = self.matcher.search(user_text=query, user_embedding=user_emb, top_k=top_k)
        filtered = [item for item in results if float(item.get("confidence", 0.0)) >= threshold]
        if not filtered and results:
            filtered = results[:1]
        citations = []
        passages = []
        for item in filtered:
            passages.append(item.get("answer_text", ""))
            citations.append({
                "source": f"intent:{item.get('intent_name', 'unknown')}",
                "content": item.get("answer_text", ""),
                "score": float(item.get("confidence", 0.0)),
            })
        return {
            "ok": bool(filtered),
            "source": "KB",
            "matches": filtered,
            "passages": passages,
            "citations": citations,
            "message": passages[0] if passages else "Không tìm thấy tri thức phù hợp trong database.",
        }

    def tool_get_elevator_status(self, elevator_id: int = 1) -> Dict[str, Any]:
        status = {
            "elevator_id": elevator_id,
            "floor": 5,
            "direction": "UP",
            "door": "CLOSED",
            "people_count": 4,
            "overload": False,
            "status": "NORMAL",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {
            "ok": True,
            "source": "ELEVATOR_STATUS",
            "status_data": status,
            "message": (
                f"Thang máy {elevator_id} đang ở tầng {status['floor']}, hướng {status['direction']}, "
                f"cửa {status['door']}, số người {status['people_count']}, quá tải: {'có' if status['overload'] else 'không'}."
            ),
        }

    def tool_call_elevator(
        self,
        elevator_id: int = 1,
        from_floor: Optional[int] = None,
        target_floor: Optional[int] = None,
        direction: str = "up",
    ) -> Dict[str, Any]:
        if from_floor is None:
            return {
                "ok": False,
                "source": "COMMAND",
                "message": "Bạn cần chỉ rõ tầng gọi thang, ví dụ: gọi thang tại tầng 3.",
            }
        eta = max(8, abs((from_floor or 5) - 5) * 4)
        command_id = uuid.uuid4().hex[:10]
        return {
            "ok": True,
            "source": "COMMAND",
            "command": {
                "command_id": command_id,
                "elevator_id": elevator_id,
                "from_floor": from_floor,
                "target_floor": target_floor,
                "direction": direction,
                "eta_seconds": eta,
                "mode": "SIMULATED",
            },
            "message": (
                f"Đã mô phỏng gọi thang máy {elevator_id} tại tầng {from_floor} theo hướng {direction}. "
                f"ETA dự kiến khoảng {eta} giây."
            ),
        }

    def tool_general_llm(self, query: str, context_blocks: Optional[List[str]] = None, memory_summary: str = "") -> Dict[str, Any]:
        answer = self.ollama.chat(query, context_blocks=context_blocks or [], memory_summary=memory_summary)
        if answer == FALLBACK_TEXT:
            return {
                "ok": False,
                "source": "LLM",
                "message": FALLBACK_TEXT,
            }
        return {
            "ok": True,
            "source": "LLM",
            "message": answer,
        }
