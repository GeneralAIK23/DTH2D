import re
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
    text = req.text or ""
    q = (req.question or "").lower()

    # Thử dùng Gemini trước, nếu lỗi key/quota thì chuyển fallback
    try:
        answer = llm.answer_question(req.question, text, req.context_summary)
        if answer:
            return AskResponse(answer=answer)
    except Exception as e:
        print(f"[ASK] Gemini error, fallback mode: {e}")

    # Hỏi deadline / thời hạn
    if "deadline" in q or "hạn" in q or "ngày nào" in q or "thời hạn" in q:
        m = re.search(
            r"(trước\s+\d{1,2}\s*giờ(?:\s*\d{1,2}\s*phút)?[,]?\s*ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}|ngày\s+\d{1,2}/\d{1,2}/\d{4}|ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})",
            text,
            re.IGNORECASE
        )
        return AskResponse(answer=m.group(0) if m else "Trong văn bản chưa thấy deadline rõ ràng.")

    # Hỏi người ký
    if "ai ký" in q or "người ký" in q or "ký" in q:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        signer = None
        for line in reversed(lines[-20:]):
            if len(line.split()) >= 2 and not line.isupper():
                signer = line
                break
        return AskResponse(answer=f"Người ký dự kiến là: {signer}" if signer else "Chưa xác định được người ký trong văn bản.")

    # Hỏi việc cần làm / checklist
    if "việc cần làm" in q or "cần làm" in q or "checklist" in q or "những việc" in q:
        tasks = re.findall(r"\d+\.\s+(.+?)(?=\n\d+\.|\n\n|$)", text, re.DOTALL)
        if tasks:
            cleaned = [re.sub(r"\s+", " ", t).strip() for t in tasks[:6]]
            answer = "Các việc cần làm gồm:\n" + "\n".join([f"- {t}" for t in cleaned])
            return AskResponse(answer=answer)
        return AskResponse(answer="Văn bản yêu cầu người nhận đọc, xử lý nội dung chính và thực hiện đúng thời hạn.")

    # Hỏi văn bản nói gì / tóm tắt
    if "nói gì" in q or "tóm tắt" in q or "nội dung" in q:
        if req.context_summary:
            return AskResponse(answer=req.context_summary)
        return AskResponse(answer=text[:700] if text else "Chưa có nội dung văn bản.")

    return AskResponse(
        answer="Tôi đã nhận câu hỏi. Ở chế độ fallback, tôi có thể trả lời các câu như: văn bản nói gì, deadline là ngày nào, ai là người ký, và những việc cần làm là gì."
    )

