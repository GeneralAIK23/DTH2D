from typing import Any
from app.agents.base import BaseAgent
from app.services.file_reader import extract_text_from_file


class DocumentExtractionAgent(BaseAgent):
    name = "DocumentExtractionAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        filename = state["filename"]
        data = state["file_bytes"]
        text, file_type, pages, warnings = extract_text_from_file(filename, data)
        state["text"] = text
        state["file_type"] = file_type
        state["pages"] = pages
        state.setdefault("warnings", []).extend(warnings)
        state.setdefault("trace", []).append({
            "agent": self.name,
            "status": "done",
            "detail": f"Đã đọc file {file_type}, lấy được {len(text)} ký tự."
        })
        return state
