from typing import Any

from app.agents.extraction_agent import DocumentExtractionAgent
from app.agents.llm_analysis_agent import LLMAnalysisAgent
from app.agents.rule_agents import MetadataAgent, SummaryAgent, TaskAgent, RiskCheckAgent, FinalReportAgent
from app.models import AnalysisResult


class DocuMindPipeline:
    def __init__(self) -> None:
        self.agents = [
            DocumentExtractionAgent(),
            LLMAnalysisAgent(),
            MetadataAgent(),
            SummaryAgent(),
            TaskAgent(),
            RiskCheckAgent(),
            FinalReportAgent(),
        ]

    def run(self, filename: str, file_bytes: bytes) -> AnalysisResult:
        state: dict[str, Any] = {
            "filename": filename,
            "file_bytes": file_bytes,
            "warnings": [],
            "trace": [],
        }
        for agent in self.agents:
            state = agent.run(state)

        text = state.get("text", "")
        return AnalysisResult(
            metadata=state["metadata"],
            summary=state["summary"],
            key_points=state["key_points"],
            tasks=state["tasks"],
            risks=state["risks"],
            answer_suggestions=state["answer_suggestions"],
            extracted_text_preview=text[:2500],
            agent_trace=state["trace"],
            raw_ai=state.get("ai_result"),
        )
