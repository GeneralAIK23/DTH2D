import re
from typing import Any
from app.agents.base import BaseAgent


def first_match(patterns: list[str], text: str, default: str = "Chưa tìm thấy") -> str:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.M)
        if m:
            value = next((g for g in m.groups() if g), "").strip(" :;,.\n\t")
            if value:
                return value[:160]
    return default


class MetadataAgent(BaseAgent):
    name = "MetadataAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        if state.get("ai_result", {}).get("metadata"):
            state["metadata"] = state["ai_result"]["metadata"]
        else:
            text = state.get("text", "")
            lower = text.lower()
            doc_type = "Không xác định"
            for t in ["quyết định", "công văn", "thông báo", "kế hoạch", "biên bản", "tờ trình"]:
                if t in lower:
                    doc_type = t.title()
                    break
            state["metadata"] = {
                "document_type": doc_type,
                "document_number": first_match([r"(?:Số|SỐ)\s*[: ]\s*([^\n]+)", r"(\d+\/[A-ZĐ\-0-9\/]+)"], text),
                "issued_date": first_match([r"ngày\s+(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})", r"(\d{1,2}\/\d{1,2}\/\d{4})"], text),
                "agency": first_match([r"^(ỦY BAN NHÂN DÂN[^\n]+)", r"^(TRƯỜNG[^\n]+)", r"^(CÔNG TY[^\n]+)", r"^(BỘ[^\n]+)"], text),
                "signer": first_match([r"(?:KT\.|TM\.)?\s*(?:CHỦ TỊCH|GIÁM ĐỐC|TRƯỞNG PHÒNG|HIỆU TRƯỞNG)?\s*\n\s*([A-ZÀ-Ỹ][A-ZÀ-Ỹ\s]{5,})\s*$"], text),
                "deadline": first_match([r"(?:trước ngày|đến ngày|chậm nhất ngày|hạn cuối ngày)\s*([^\.\n]+)", r"(?:thời hạn|deadline)\s*[: ]\s*([^\.\n]+)"], text),
            }
        state.setdefault("trace", []).append({"agent": self.name, "status": "done", "detail": "Đã trích xuất thông tin hành chính."})
        return state


class SummaryAgent(BaseAgent):
    name = "SummaryAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        ai = state.get("ai_result") or {}
        if ai.get("summary"):
            state["summary"] = ai["summary"]
            state["key_points"] = ai.get("key_points", [])
        else:
            text = re.sub(r"\s+", " ", state.get("text", "")).strip()
            sentences = re.split(r"(?<=[.!?])\s+", text)
            picked = [s for s in sentences if len(s) > 30][:5]
            state["summary"] = " ".join(picked)[:1200] or "Chưa đủ nội dung để tóm tắt."
            state["key_points"] = [s[:180] for s in picked[:4]] or ["Chưa xác định được ý chính."]
        state.setdefault("trace", []).append({"agent": self.name, "status": "done", "detail": "Đã tạo tóm tắt và ý chính."})
        return state


class TaskAgent(BaseAgent):
    name = "TaskAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        ai = state.get("ai_result") or {}
        if ai.get("tasks"):
            state["tasks"] = ai["tasks"]
        else:
            text = state.get("text", "")
            deadline = state.get("metadata", {}).get("deadline", "Chưa xác định")
            task_patterns = [
                r"(?:đề nghị|yêu cầu|giao|phân công)\s+([^\.\n]+)",
                r"(?:thực hiện|triển khai|báo cáo|rà soát)\s+([^\.\n]+)",
            ]
            tasks = []
            for p in task_patterns:
                for m in re.finditer(p, text, flags=re.I):
                    title = m.group(0).strip()
                    if len(title) > 18:
                        tasks.append({"title": title[:180], "owner": "Chưa xác định", "due_date": deadline, "priority": "Trung bình"})
                    if len(tasks) >= 5:
                        break
                if len(tasks) >= 5:
                    break
            state["tasks"] = tasks or [{"title": "Đọc và xử lý nội dung chính của văn bản", "owner": "Người phụ trách", "due_date": deadline, "priority": "Trung bình"}]
        state.setdefault("trace", []).append({"agent": self.name, "status": "done", "detail": "Đã tạo danh sách việc cần làm."})
        return state


class RiskCheckAgent(BaseAgent):
    name = "RiskCheckAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        ai = state.get("ai_result") or {}
        if ai.get("risks"):
            state["risks"] = ai["risks"]
        else:
            metadata = state.get("metadata", {})
            risks = []
            checks = [
                ("deadline", "Văn bản chưa thấy thời hạn xử lý.", "Bổ sung thời hạn rõ ràng để tiện theo dõi tiến độ."),
                ("agency", "Chưa thấy cơ quan/đơn vị ban hành.", "Kiểm tra lại phần đầu văn bản."),
                ("signer", "Chưa thấy thông tin người ký.", "Bổ sung người ký/chức vụ nếu đây là văn bản phát hành chính thức."),
                ("document_number", "Chưa thấy số/ký hiệu văn bản.", "Bổ sung số văn bản để quản lý và tra cứu."),
            ]
            for key, issue, suggestion in checks:
                if metadata.get(key, "Chưa tìm thấy") in ["Chưa tìm thấy", "Chưa xác định", ""]:
                    risks.append({"level": "Trung bình", "issue": issue, "suggestion": suggestion})
            state["risks"] = risks or [{"level": "Thấp", "issue": "Chưa phát hiện thiếu sót lớn ở mức demo.", "suggestion": "Nên kiểm tra lại thủ công trước khi ban hành."}]
        state.setdefault("trace", []).append({"agent": self.name, "status": "done", "detail": "Đã kiểm tra thiếu sót/rủi ro cơ bản."})
        return state


class FinalReportAgent(BaseAgent):
    name = "FinalReportAgent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        ai = state.get("ai_result") or {}
        state["answer_suggestions"] = ai.get("answer_suggestions") or [
            "Văn bản này nói gì?",
            "Deadline là ngày nào?",
            "Ai là đơn vị phụ trách?",
            "Những việc cần làm là gì?",
        ]
        state.setdefault("trace", []).append({"agent": self.name, "status": "done", "detail": "Đã đóng gói kết quả trả về Web."})
        return state
