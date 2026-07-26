from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agents.pipeline import DocuMindPipeline
from app.config import CORS_ORIGINS, MAX_UPLOAD_MB
from app.models import AnalysisResult, AskRequest, AskResponse
from app.services.llm_client import GeminiClient

app = FastAPI(
    title="DocuMind AI API",
    description="Backend đọc PDF/DOCX/TXT/ảnh, chạy agent pipeline và gọi Gemini API để tóm tắt văn bản hành chính.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = DocuMindPipeline()
llm = GeminiClient()


@app.get("/")
def root() -> dict:
    return {
        "message": "DocuMind AI backend is running",
        "pipeline": [agent.name for agent in pipeline.agents],
        "gemini_enabled": llm.enabled,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)) -> AnalysisResult:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File quá lớn. Tối đa {MAX_UPLOAD_MB}MB.")
    try:
        return pipeline.run(file.filename or "uploaded-file", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {exc}") from exc


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    answer = llm.answer_question(req.question, req.text, req.context_summary)
    if answer:
        return AskResponse(answer=answer)

    # fallback không có Gemini key
    q = req.question.lower()
    text = req.text
    if "deadline" in q or "hạn" in q:
        import re
        m = re.search(r"(?:trước ngày|đến ngày|chậm nhất ngày|hạn cuối ngày)\s*([^\.\n]+)", text, flags=re.I)
        return AskResponse(answer=m.group(0) if m else "Trong văn bản chưa thấy deadline rõ ràng.")
    if "tóm tắt" in q or "nói gì" in q:
        return AskResponse(answer=req.context_summary or text[:700] or "Chưa có nội dung văn bản.")
    return AskResponse(answer="Bản fallback chưa đủ AI để trả lời sâu. Hãy thêm GEMINI_API_KEY để hỏi đáp tốt hơn.")
