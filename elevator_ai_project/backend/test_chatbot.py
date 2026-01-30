# backend/test_chatbot.py
from backend.chatbot_engine import ChatbotEngine

def test_greeting_db():
    e = ChatbotEngine()
    r = e.handle("xin chao")
    assert "sunybot" in r["answer"].lower()
    assert r["source"] in ["DB_PROMPT", "LLM", "FALLBACK"]

def test_employee_code():
    e = ChatbotEngine()
    r = e.handle("NV020")
    assert "Nguyen Chan Huy" in r["answer"]
    assert r["source"] == "EMPLOYEE"

def test_faq_speed():
    e = ChatbotEngine()
    r = e.handle("Toc do thang may la bao nhieu")
    assert "1.2" in r["answer"]

