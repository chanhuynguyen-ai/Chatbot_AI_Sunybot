import json
from typing import Any, Dict, Optional

from backend.agent import AgentRuntime
from backend.agent.tool_registry import ToolRegistry
from backend.embedding_service import EmbeddingService
from backend.ollama_service import OllamaService
from backend.semantic_matcher import SemanticMatcher
from config.db_config import db


class ChatbotEngine:
    def __init__(self):
        self.matcher = SemanticMatcher()
        self.matcher.load_from_db()
        self.embedder = EmbeddingService()
        self.ollama = OllamaService()
        self.tool_registry = ToolRegistry(matcher=self.matcher, embedder=self.embedder, ollama=self.ollama)
        self.agent = AgentRuntime(tool_registry=self.tool_registry)

    def reload_knowledge(self):
        self.matcher.load_from_db()

    def log_chat(self, result: Dict[str, Any], question: str):
        conn = db.connect()
        trace_json = json.dumps(result.get("tool_trace", []), ensure_ascii=False)
        payload = (
            result.get("session_id"),
            question,
            result.get("intent"),
            float(result.get("confidence") or 0.0),
            result.get("source"),
            (result.get("answer") or "")[:250],
            trace_json,
            int(len(result.get("tool_trace", []))),
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_logs(
                        session_id, question, intent_name, confidence, source,
                        answer_preview, tool_trace_json, tool_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    payload,
                )
        finally:
            conn.close()

    def handle(self, user_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        result = self.agent.run(user_text, session_id=session_id)
        self.log_chat(result, user_text)
        return result

    def handle_request(self, req) -> Dict[str, Any]:
        message = getattr(req, "message", "") or getattr(req, "question", "")
        session_id = getattr(req, "session_id", None)
        return self.handle(message, session_id=session_id)

    def get_elevator_status(self, elevator_id: int = 1) -> Dict[str, Any]:
        return self.tool_registry.tool_get_elevator_status(elevator_id=elevator_id)

    def call_elevator(
        self,
        elevator_id: int = 1,
        from_floor: Optional[int] = None,
        target_floor: Optional[int] = None,
        direction: str = "up",
    ) -> Dict[str, Any]:
        return self.tool_registry.tool_call_elevator(
            elevator_id=elevator_id,
            from_floor=from_floor,
            target_floor=target_floor,
            direction=direction,
        )

    def healthcheck(self) -> Dict[str, Any]:
        db_ok = db.test_connection()
        return {
            "db_ok": db_ok,
            "db_backend": "postgresql",
            "matcher_items": self.matcher.item_count,
            "ollama_ok": self.ollama.healthcheck(),
        }
