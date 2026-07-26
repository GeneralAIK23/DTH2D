# DocuMind AI - Fullstack Agent Web App

Bản này không còn là demo sơ sài. Đây là project **React + FastAPI + Agent Pipeline + Gemini API**.

## Tính năng chính

- Web App bằng React/Vite.
- Backend API bằng FastAPI.
- Upload và đọc file: PDF, DOCX, TXT, MD, PNG, JPG.
- PDF dùng `pypdf` để trích text.
- Word dùng `python-docx` để đọc nội dung.
- Ảnh dùng `pytesseract` để OCR.
- Agent pipeline gồm:
  1. `DocumentExtractionAgent`: đọc file.
  2. `LLMAnalysisAgent`: gọi Gemini API.
  3. `MetadataAgent`: trích loại văn bản, số hiệu, ngày, cơ quan, người ký, deadline.
  4. `SummaryAgent`: tóm tắt và rút ý chính.
  5. `TaskAgent`: tạo việc cần làm.
  6. `RiskCheckAgent`: cảnh báo thiếu sót.
  7. `FinalReportAgent`: đóng gói kết quả trả về Web.
- Có hỏi đáp với văn bản.
- Có log agent pipeline để demo với giám khảo.
- Nếu chưa có Gemini key, backend vẫn chạy fallback rule-based.

---

## Cấu trúc thư mục

```txt
documind-fullstack-agent/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── main.py
│   │   └── models.py
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
└── README.md
```

---

## Cách chạy Backend

Mở terminal trong VS Code:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Backend chạy tại:

```txt
http://localhost:8000
```

Docs API:

```txt
http://localhost:8000/docs
```

### Gắn Gemini API thật

Mở file `backend/.env` và sửa:

```env
GEMINI_API_KEY=key_that_cua_ban
GEMINI_MODEL=gemini-2.5-flash
```

Không có key thì vẫn chạy fallback, nhưng AI sẽ không mạnh bằng.

---

## Cách chạy Frontend

Mở terminal khác:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Web chạy tại:

```txt
http://localhost:5173
```

---

## Cách demo với giám khảo

1. Mở web `http://localhost:5173` hoặc domain thật `app.documind.vn`.
2. Upload file PDF/DOCX văn bản hành chính.
3. Bấm **Phân tích văn bản**.
4. Hệ thống hiển thị:
   - Loại văn bản.
   - Số hiệu.
   - Ngày ban hành.
   - Cơ quan ban hành.
   - Người ký.
   - Deadline.
   - Tóm tắt.
   - Ý chính.
   - Việc cần làm.
   - Cảnh báo thiếu sót.
5. Mở phần **log agent pipeline** để chứng minh hệ thống có agent xử lý bên trong.
6. Hỏi thử: “Deadline là ngày nào?” hoặc “Văn bản này yêu cầu làm gì?”.

---

## Triển khai domain thật

Gợi ý:

- Frontend: Vercel → `app.documind.vn`
- Backend: Render/Railway/VPS → `api.documind.vn`
- Website giới thiệu: `documind.vn`

Cấu hình frontend production:

```env
VITE_API_BASE_URL=https://api.documind.vn
```

Cấu hình backend production:

```env
CORS_ORIGINS=https://app.documind.vn,https://documind.vn
```

---

## Lưu ý OCR ảnh

Nếu muốn OCR ảnh tiếng Việt trên Windows, cần cài thêm Tesseract OCR và gói ngôn ngữ `vie`.
Nếu chỉ upload PDF/DOCX có text thì không cần OCR.

