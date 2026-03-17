import re
from typing import List, Optional

from backend.schemas import AgentPlan, ToolCall
from backend.text_utils import normalize_vi
from backend.employee_service import is_employee_code


class Planner:
    STATUS_KEYWORDS = [
        "trang thai", "hien tai", "thang may dang o dau", "dang o tang", "qua tai", "cua", "status"
    ]
    CALL_KEYWORDS = ["goi thang", "call elevator", "len tang", "xuong tang", "goi cabin"]
    EMPLOYEE_HINTS = ["nhan vien", "email", "so dien thoai", "phong ban", "ma nhan vien", "thong tin"]
    DOMAIN_KEYWORDS = [
        "thang may", "elevator", "sos", "bao tri", "tang", "cabin", "cua", "qua tai", "ky thuat"
    ]

    def create_plan(self, user_text: str, history: Optional[List[dict]] = None) -> AgentPlan:
        norm = normalize_vi(user_text)
        history = history or []

        if is_employee_code(user_text):
            return AgentPlan(
                intent="employee_lookup",
                plan=["Tra cứu nhân viên theo mã."],
                tool_calls=[ToolCall(tool_name="employee_lookup", args={"query": user_text}, reason="Mã nhân viên hợp lệ")],
                confidence=0.99,
            )

        if self._looks_like_employee_query(norm, user_text):
            return AgentPlan(
                intent="employee_lookup",
                plan=["Tra cứu nhân viên theo tên hoặc mô tả."],
                tool_calls=[ToolCall(tool_name="employee_lookup", args={"query": user_text}, reason="Câu hỏi có dấu hiệu tra cứu nhân viên")],
                confidence=0.90,
            )

        if self._has_any(norm, self.STATUS_KEYWORDS):
            return AgentPlan(
                intent="elevator_status",
                plan=["Lấy trạng thái thang máy hiện tại."],
                tool_calls=[ToolCall(tool_name="get_elevator_status", args=self._parse_status_args(user_text), reason="Câu hỏi về trạng thái thang máy")],
                confidence=0.92,
            )

        if self._has_any(norm, self.CALL_KEYWORDS):
            return AgentPlan(
                intent="call_elevator",
                plan=["Phân tích yêu cầu gọi thang và mô phỏng gửi lệnh."],
                tool_calls=[ToolCall(tool_name="call_elevator", args=self._parse_call_args(user_text), reason="Người dùng muốn gọi thang")],
                confidence=0.90,
            )

        if self._has_any(norm, self.DOMAIN_KEYWORDS):
            return AgentPlan(
                intent="knowledge_lookup",
                plan=["Tìm tri thức liên quan trong knowledge base.", "Nếu chưa đủ thì dùng LLM diễn giải dựa trên kết quả tìm được."],
                tool_calls=[ToolCall(tool_name="kb_search", args={"query": user_text, "top_k": 3}, reason="Câu hỏi nằm trong domain thang máy")],
                confidence=0.80,
            )

        return AgentPlan(
            intent="general_llm",
            plan=["Trả lời bằng LLM nhưng giữ giới hạn domain của Sunybot."],
            tool_calls=[ToolCall(tool_name="general_llm", args={"query": user_text}, reason="Không khớp tool chuyên biệt")],
            confidence=0.55,
        )

    def _has_any(self, text: str, keywords: List[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _looks_like_employee_query(self, norm: str, original: str) -> bool:
        if self._has_any(norm, self.EMPLOYEE_HINTS):
            return True
        return len(original.split()) >= 2 and any(token in norm for token in ["nhan vien", "ky su", "truong phong"])

    def _parse_status_args(self, user_text: str) -> dict:
        m = re.search(r"(?:thang|elevator)\s*(\d+)", user_text, flags=re.IGNORECASE)
        elevator_id = int(m.group(1)) if m else 1
        return {"elevator_id": elevator_id}

    def _parse_call_args(self, user_text: str) -> dict:
        norm = normalize_vi(user_text)
        floors = re.findall(r"(?:tang|floor)\s*(\d+)", norm)
        direction = "up"
        if "xuong" in norm:
            direction = "down"
        if "len" in norm:
            direction = "up"
        result = {
            "elevator_id": 1,
            "from_floor": int(floors[0]) if floors else None,
            "target_floor": int(floors[1]) if len(floors) > 1 else None,
            "direction": direction,
        }
        return result
