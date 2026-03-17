from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional


class ConversationMemoryStore:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._store: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=self.max_turns))

    def add_turn(self, session_id: str, role: str, content: str):
        if not session_id or not content:
            return
        self._store[session_id].append({"role": role, "content": content})

    def get_history(self, session_id: Optional[str]) -> List[dict]:
        if not session_id:
            return []
        return list(self._store.get(session_id, []))

    def build_summary(self, session_id: Optional[str]) -> str:
        history = self.get_history(session_id)
        if not history:
            return ""
        last_items = history[-4:]
        parts = [f"{item['role']}: {item['content']}" for item in last_items]
        return " | ".join(parts)
