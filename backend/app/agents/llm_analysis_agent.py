from typing import Any
from app.agents.base import BaseAgent
from app.services.llm_client import GeminiClient


class LLMAnalysisAgent(BaseAgent):
    name = "LLMAnalysisAgent"

    def __init__(self) -> None:
        self.client = GeminiClient()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        text = state.get("text", "")
        ai_result = self.client.analyze_document(text)
        state["ai_result"] = ai_result
        state.setdefault("trace", []).append({
            "agent": self.name,
            "status": "done" if ai_result else "fallback",
            "detail": "Đã gọi Gemini API và nhận JSON." if ai_result else "Chưa có GEMINI_API_KEY hoặc AI không trả JSON, dùng agent rule-based."
        })
        return state
