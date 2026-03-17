import json
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.agent.memory_store import ConversationMemoryStore
from backend.agent.planner import Planner
from backend.agent.safety import SafetyGuardrails
from backend.agent.tool_registry import ToolRegistry
from backend.schemas import Citation, ChatResponse, ToolTrace


class AgentRuntime:
    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry
        self.memory = ConversationMemoryStore(max_turns=12)
        self.safety = SafetyGuardrails()
        self.planner = Planner()

    def run(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_id = session_id or uuid.uuid4().hex
        user_text = (message or "").strip()
        if not user_text:
            return ChatResponse(
                answer="Bạn vui lòng nhập câu hỏi.",
                source="SYSTEM",
                intent="empty_input",
                confidence=1.0,
                session_id=session_id,
            ).dict()

        self.memory.add_turn(session_id, "user", user_text)
        memory_summary = self.memory.build_summary(session_id)
        precheck = self.safety.precheck(user_text)
        if precheck["status"] == "blocked":
            answer = precheck["answer"]
            self.memory.add_turn(session_id, "assistant", answer)
            return ChatResponse(
                answer=answer,
                source="SAFETY",
                intent=precheck["intent"],
                confidence=1.0,
                session_id=session_id,
                memory_summary=memory_summary,
                status="blocked",
            ).dict()

        plan = self.planner.create_plan(user_text, history=self.memory.get_history(session_id))
        traces: List[ToolTrace] = []
        citations: List[Citation] = []
        tool_results: List[Dict[str, Any]] = []

        if precheck["status"] == "emergency" and not any(call.tool_name == "get_elevator_status" for call in plan.tool_calls):
            from backend.schemas import ToolCall
            plan.tool_calls.insert(0, ToolCall(tool_name="get_elevator_status", args={"elevator_id": 1}, reason="Lấy trạng thái để hỗ trợ khẩn cấp"))

        for tool_call in plan.tool_calls:
            if tool_call is None:
                continue
            if not self.safety.allow_tool(tool_call.tool_name):
                traces.append(ToolTrace(tool_name=tool_call.tool_name, args=tool_call.args, status="blocked", summary="Tool bị guardrail chặn."))
                continue
            started = time.time()
            try:
                result = self.tools.run(tool_call.tool_name, tool_call.args)
                duration_ms = int((time.time() - started) * 1000)
                traces.append(
                    ToolTrace(
                        tool_name=tool_call.tool_name,
                        args=tool_call.args,
                        status="ok" if result.get("ok") else "error",
                        duration_ms=duration_ms,
                        summary=result.get("message", "")[:220],
                    )
                )
                tool_results.append({"tool": tool_call.tool_name, "result": result})
                for item in result.get("citations", []):
                    citations.append(Citation(**item))
            except Exception as exc:
                duration_ms = int((time.time() - started) * 1000)
                traces.append(
                    ToolTrace(
                        tool_name=tool_call.tool_name,
                        args=tool_call.args,
                        status="error",
                        duration_ms=duration_ms,
                        summary=f"Tool lỗi: {exc}",
                    )
                )

        response = self._compose_response(
            user_text=user_text,
            session_id=session_id,
            plan_intent=plan.intent,
            plan_confidence=plan.confidence,
            precheck=precheck,
            tool_results=tool_results,
            traces=traces,
            citations=citations,
            memory_summary=memory_summary,
        )
        self.memory.add_turn(session_id, "assistant", response["answer"])
        return response

    def _compose_response(
        self,
        user_text: str,
        session_id: str,
        plan_intent: str,
        plan_confidence: float,
        precheck: Dict[str, str],
        tool_results: List[Dict[str, Any]],
        traces: List[ToolTrace],
        citations: List[Citation],
        memory_summary: str,
    ) -> Dict[str, Any]:
        source = "AGENT"
        answer = "Sunybot hiện chưa có đủ dữ liệu để trả lời chính xác câu hỏi này."
        requires_human = False

        result_map = {item["tool"]: item["result"] for item in tool_results}

        if plan_intent == "employee_lookup":
            employee_result = result_map.get("employee_lookup", {})
            answer = employee_result.get("message", answer)
            source = employee_result.get("source", "EMPLOYEE")
        elif plan_intent == "elevator_status":
            status_result = result_map.get("get_elevator_status", {})
            answer = status_result.get("message", answer)
            source = status_result.get("source", "ELEVATOR_STATUS")
        elif plan_intent == "call_elevator":
            call_result = result_map.get("call_elevator", {})
            answer = call_result.get("message", answer)
            source = call_result.get("source", "COMMAND")
        elif plan_intent == "knowledge_lookup":
            kb_result = result_map.get("kb_search", {})
            if kb_result.get("ok"):
                context_blocks = kb_result.get("passages", [])
                llm_result = self.tools.run(
                    "general_llm",
                    {"query": user_text, "context_blocks": context_blocks, "memory_summary": memory_summary},
                )
                traces.append(ToolTrace(tool_name="general_llm", args={"query": user_text}, status="ok" if llm_result.get("ok") else "error", summary=llm_result.get("message", "")[:220]))
                answer = llm_result.get("message") or kb_result.get("message", answer)
                source = "AGENT"
            else:
                llm_result = self.tools.run(
                    "general_llm",
                    {"query": user_text, "context_blocks": [], "memory_summary": memory_summary},
                )
                traces.append(ToolTrace(tool_name="general_llm", args={"query": user_text}, status="ok" if llm_result.get("ok") else "error", summary=llm_result.get("message", "")[:220]))
                answer = llm_result.get("message", answer)
                source = llm_result.get("source", "LLM")
        else:
            llm_result = result_map.get("general_llm", {})
            answer = llm_result.get("message", answer)
            source = llm_result.get("source", "LLM")

        if precheck.get("status") == "emergency":
            status_result = result_map.get("get_elevator_status", {})
            suffix = status_result.get("message", "")
            answer = f"{precheck['answer']} {suffix}".strip()
            source = "SAFETY"
            requires_human = True

        return ChatResponse(
            answer=answer,
            source=source,
            intent=plan_intent if precheck.get("status") == "ok" else precheck.get("intent"),
            confidence=round(float(plan_confidence), 3),
            session_id=session_id,
            tool_trace=traces,
            citations=citations,
            memory_summary=self.memory.build_summary(session_id),
            requires_human=requires_human,
            status="ok" if source != "SAFETY" or precheck.get("status") == "emergency" else precheck.get("status", "ok"),
        ).dict()

    def serialize_trace(self, traces: List[ToolTrace]) -> str:
        return json.dumps([trace.dict() for trace in traces], ensure_ascii=False)
