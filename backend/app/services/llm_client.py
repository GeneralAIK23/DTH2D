import json
import re
from typing import Any, Optional

from app.config import GEMINI_API_KEY, GEMINI_MODEL


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


class GeminiClient:
    def __init__(self) -> None:
        self.enabled = bool(GEMINI_API_KEY)
        self.model = GEMINI_MODEL
        self._client = None
        if self.enabled:
            from google import genai
            self._client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze_document(self, text: str) -> Optional[dict[str, Any]]:
        if not self.enabled or not self._client:
            return None

        prompt = f"""
Bạn là DocuMind AI, trợ lý đọc và tóm tắt văn bản hành chính tiếng Việt.
Hãy phân tích văn bản sau và chỉ trả về JSON hợp lệ, không markdown.

Yêu cầu JSON đúng schema:
{{
  "metadata": {{
    "document_type": "loại văn bản",
    "document_number": "số/ký hiệu văn bản hoặc Chưa tìm thấy",
    "issued_date": "ngày ban hành hoặc Chưa tìm thấy",
    "agency": "cơ quan/đơn vị ban hành hoặc Chưa tìm thấy",
    "signer": "người ký hoặc Chưa tìm thấy",
    "deadline": "thời hạn xử lý hoặc Chưa tìm thấy"
  }},
  "summary": "tóm tắt 4-6 câu, rõ ràng, dễ hiểu",
  "key_points": ["ý chính 1", "ý chính 2", "ý chính 3"],
  "tasks": [
    {{"title": "việc cần làm", "owner": "đơn vị/người phụ trách", "due_date": "deadline", "priority": "Cao/Trung bình/Thấp"}}
  ],
  "risks": [
    {{"level": "Cao/Trung bình/Thấp", "issue": "thiếu sót/rủi ro", "suggestion": "gợi ý xử lý"}}
  ],
  "answer_suggestions": ["Deadline là ngày nào?", "Ai phụ trách?", "Văn bản yêu cầu làm gì?"]
}}

Nguyên tắc:
- Không bịa thông tin. Không thấy thì ghi "Chưa tìm thấy".
- Ưu tiên deadline, nhiệm vụ, cơ quan, người ký.
- Nếu văn bản dài, tóm tắt theo nội dung quan trọng nhất.

Văn bản:
{text[:30000]}
""".strip()
        response = self._client.models.generate_content(model=self.model, contents=prompt)
        return _extract_json(getattr(response, "text", "") or "")

    def answer_question(self, question: str, text: str, context_summary: Optional[str] = None) -> Optional[str]:
        if not self.enabled or not self._client:
            return None
        prompt = f"""
Bạn là DocuMind AI. Trả lời câu hỏi dựa CHỈ trên văn bản được cung cấp.
Nếu không tìm thấy thông tin, trả lời: "Trong văn bản chưa thấy thông tin này."

Tóm tắt trước đó: {context_summary or "Không có"}

Câu hỏi: {question}

Văn bản:
{text[:30000]}
""".strip()
        response = self._client.models.generate_content(model=self.model, contents=prompt)
        return (getattr(response, "text", "") or "").strip()
