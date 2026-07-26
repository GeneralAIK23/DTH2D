from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    filename: str
    file_type: str
    text: str
    pages: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)


class Metadata(BaseModel):
    document_type: str = "Không xác định"
    document_number: str = "Chưa tìm thấy"
    issued_date: str = "Chưa tìm thấy"
    agency: str = "Chưa tìm thấy"
    signer: str = "Chưa tìm thấy"
    deadline: str = "Chưa tìm thấy"


class TaskItem(BaseModel):
    title: str
    owner: str = "Chưa xác định"
    due_date: str = "Chưa xác định"
    priority: str = "Trung bình"


class RiskItem(BaseModel):
    level: str
    issue: str
    suggestion: str


class AgentTrace(BaseModel):
    agent: str
    status: str
    detail: str


class AnalysisResult(BaseModel):
    metadata: Metadata
    summary: str
    key_points: List[str]
    tasks: List[TaskItem]
    risks: List[RiskItem]
    answer_suggestions: List[str]
    extracted_text_preview: str
    agent_trace: List[AgentTrace]
    raw_ai: Optional[Any] = None


class AskRequest(BaseModel):
    question: str
    text: str
    context_summary: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
