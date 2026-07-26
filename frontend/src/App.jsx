import { useMemo, useState } from 'react';
import { Upload, FileText, Bot, AlertTriangle, CheckCircle2, Send, Download } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const sampleQuestions = [
  'Văn bản này nói gì?',
  'Deadline là ngày nào?',
  'Ai là người ký?',
  'Những việc cần làm là gì?'
];

function InfoCard({ title, value }) {
  return (
    <div className="info-card">
      <span>{title}</span>
      <strong>{value || 'Chưa tìm thấy'}</strong>
    </div>
  );
}

function ListBlock({ title, items, renderItem }) {
  return (
    <section className="block">
      <h3>{title}</h3>
      {!items?.length ? <p className="muted">Chưa có dữ liệu.</p> : (
        <div className="list">
          {items.map((item, index) => (
            <div className="list-item" key={index}>{renderItem ? renderItem(item, index) : item}</div>
          ))}
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);

  const canAsk = useMemo(() => result?.extracted_text_preview && question.trim(), [result, question]);

  async function analyzeDocument() {
    if (!file) {
      setError('Hãy chọn file PDF, DOCX, TXT, PNG hoặc JPG trước.');
      return;
    }
    setError('');
    setLoading(true);
    setResult(null);
    setMessages([]);

    try {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: form,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Lỗi phân tích văn bản.');
      setResult(data);
    } catch (err) {
      setError(err.message || 'Không xử lý được văn bản. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }

  async function askQuestion(customQuestion) {
    const q = (customQuestion || question).trim();
    if (!q || !result) return;
    setAsking(true);
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setQuestion('');

    try {
      const response = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          text: result.extracted_text_preview,
          context_summary: result.summary,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Lỗi hỏi đáp.');
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Lỗi: ${err.message}` }]);
    } finally {
      setAsking(false);
    }
  }

  function exportReport() {
    if (!result) return;
    const m = result.metadata;
    const content = `DOCUMIND AI - BÁO CÁO PHÂN TÍCH VĂN BẢN\n\n` +
      `Loại văn bản: ${m.document_type}\nSố văn bản: ${m.document_number}\nNgày ban hành: ${m.issued_date}\nCơ quan: ${m.agency}\nNgười ký: ${m.signer}\nDeadline: ${m.deadline}\n\n` +
      `TÓM TẮT:\n${result.summary}\n\n` +
      `Ý CHÍNH:\n${result.key_points.map((x, i) => `${i + 1}. ${x}`).join('\n')}\n\n` +
      `VIỆC CẦN LÀM:\n${result.tasks.map((x, i) => `${i + 1}. ${x.title} | Phụ trách: ${x.owner} | Hạn: ${x.due_date}`).join('\n')}\n\n` +
      `CẢNH BÁO:\n${result.risks.map((x, i) => `${i + 1}. [${x.level}] ${x.issue} - ${x.suggestion}`).join('\n')}\n`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'documind-report.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <div className="badge"><Bot size={16} /> DocuMind AI Web App</div>
          <h1>Trợ lý AI đọc, tóm tắt và kiểm tra văn bản hành chính</h1>
          <div className="hero-actions">
            <a href="#upload" className="primary-link">Dùng thử ngay</a>
          </div>
        </div>
      </header>

      <section className="layout" id="upload">
        <aside className="upload-panel">
          <h2><Upload size={20} /> Tải văn bản lên</h2>
          <label className="dropzone">
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <FileText size={34} />
            <strong>{file ? file.name : 'Chọn PDF, Word, TXT hoặc ảnh'}</strong>
            <span>Hệ thống sẽ đọc nội dung và tóm tắt tự động.</span>
          </label>
          <button className="analyze-btn" onClick={analyzeDocument} disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Phân tích văn bản'}
          </button>
          {error && <div className="error"><AlertTriangle size={18} /> {error}</div>}

        </aside>

        <section className="result-panel">
          {!result && !loading && (
            <div className="empty-state">
              <Bot size={52} />
              <h2>Chưa có kết quả</h2>
              <p>Chọn một văn bản hành chính rồi bấm phân tích để xem bản tóm tắt và các thông tin quan trọng.</p>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <div className="loader" />
              <h2>Đang phân tích văn bản...</h2>
              <p>Hệ thống đang đọc nội dung, tóm tắt và trích xuất thông tin quan trọng.</p>
            </div>
          )}

          {result && (
            <>
              <div className="result-header">
                <div>
                  <span className="success"><CheckCircle2 size={16} /> Đã phân tích xong</span>
                  <h2>Kết quả phân tích</h2>
                </div>
                <button className="secondary-btn" onClick={exportReport}><Download size={16} /> Xuất TXT</button>
              </div>

              <div className="grid-info">
                <InfoCard title="Loại văn bản" value={result.metadata.document_type} />
                <InfoCard title="Số hiệu" value={result.metadata.document_number} />
                <InfoCard title="Ngày ban hành" value={result.metadata.issued_date} />
                <InfoCard title="Cơ quan" value={result.metadata.agency} />
                <InfoCard title="Người ký" value={result.metadata.signer} />
                <InfoCard title="Deadline" value={result.metadata.deadline} />
              </div>

              <section className="block summary-block">
                <h3>Tóm tắt văn bản</h3>
                <p>{result.summary}</p>
              </section>

              <ListBlock title="Ý chính" items={result.key_points} renderItem={(item, i) => <><b>{i + 1}.</b> {item}</>} />

              <ListBlock title="Việc cần làm" items={result.tasks} renderItem={(task) => (
                <div>
                  <strong>{task.title}</strong>
                  <p>Phụ trách: {task.owner} · Hạn: {task.due_date} · Ưu tiên: {task.priority}</p>
                </div>
              )} />

              <ListBlock title="Cảnh báo / thiếu sót" items={result.risks} renderItem={(risk) => (
                <div>
                  <strong>[{risk.level}] {risk.issue}</strong>
                  <p>{risk.suggestion}</p>
                </div>
              )} />

              <section className="chat-block">
                <h3>Hỏi đáp với văn bản</h3>
                <div className="suggestions">
                  {sampleQuestions.map(q => <button key={q} onClick={() => askQuestion(q)} disabled={asking}>{q}</button>)}
                </div>
                <div className="messages">
                  {messages.map((msg, i) => (
                    <div className={`message ${msg.role}`} key={i}>{msg.content}</div>
                  ))}
                  {asking && <div className="message assistant">Đang trả lời...</div>}
                </div>
                <div className="ask-row">
                  <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Hỏi về văn bản này..." onKeyDown={(e) => e.key === 'Enter' && canAsk && askQuestion()} />
                  <button onClick={() => askQuestion()} disabled={!canAsk || asking}><Send size={16} /></button>
                </div>
              </section>
            </>
          )}
        </section>
      </section>
    </main>
  );
}
