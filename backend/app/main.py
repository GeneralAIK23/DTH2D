import re
import re
import unicodedata
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
    question = req.question or ""
    summary = req.context_summary or ""

    if not text.strip() and not summary.strip():
        return AskResponse(answer="Chua co noi dung van ban. Hay upload va phan tich van ban truoc khi hoi dap.")

    # Goi Gemini truoc de hoi dap that su theo noi dung van ban
    try:
        answer = llm.answer_question(question, text, summary)
        if answer and str(answer).strip():
            return AskResponse(answer=str(answer).strip())
    except Exception as e:
        print(f"[ASK] Gemini error, using fallback: {repr(e)}")

    # Fallback chi dung khi Gemini loi quota/key/mang
    import unicodedata as _ud

    def plain(s: str) -> str:
        s = _ud.normalize("NFD", s or "")
        s = "".join(ch for ch in s if _ud.category(ch) != "Mn")
        return s.replace("đ", "d").replace("Đ", "D").lower()

    q = plain(question)

    if "deadline" in q or "han" in q or "ngay nao" in q or "thoi han" in q:
        m = re.search(
            r"(truoc\s+\d{1,2}\s*gio(?:\s*\d{1,2}\s*phut)?[,]?\s*ngay\s+\d{1,2}\s+thang\s+\d{1,2}\s+nam\s+\d{4}|ngay\s+\d{1,2}/\d{1,2}/\d{4})",
            plain(text),
            re.IGNORECASE
        )
        return AskResponse(answer=m.group(0) if m else "Fallback: chua thay deadline ro rang trong van ban.")

    if "ai ky" in q or "nguoi ky" in q:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        signer = lines[-1] if lines else ""
        return AskResponse(answer=f"Fallback: nguoi ky du kien la {signer}" if signer else "Fallback: chua xac dinh duoc nguoi ky.")

    if "viec can lam" in q or "can lam" in q or "checklist" in q or "nhung viec" in q:
        tasks = re.findall(r"\d+\.\s+(.+?)(?=\n\d+\.|\n\n|$)", text, re.DOTALL)
        if tasks:
            cleaned = [re.sub(r"\s+", " ", t).strip() for t in tasks[:6]]
            return AskResponse(answer="Fallback - cac viec can lam:\n" + "\n".join([f"- {t}" for t in cleaned]))
        return AskResponse(answer="Fallback: van ban yeu cau nguoi nhan doc, xu ly noi dung chinh va thuc hien dung thoi han.")

    if "noi gi" in q or "tom tat" in q or "noi dung" in q or "van ban" in q:
        return AskResponse(answer=summary if summary else text[:700])

    return AskResponse(answer=summary if summary else "Fallback: da nhan cau hoi, nhung Gemini dang loi nen chi tra loi co ban theo noi dung van ban.")

