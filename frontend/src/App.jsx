import { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000/api/v1";

// ── Types ────────────────────────────────────────────────────────────────────
const ROLES = { USER: "user", BOT: "bot" };

// ── API helpers ──────────────────────────────────────────────────────────────
async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

async function fetchDocuments() {
  const res = await fetch(`${API}/documents`);
  return res.json();
}

async function deleteDocument(docId) {
  await fetch(`${API}/documents/${docId}`, { method: "DELETE" });
}

async function askQuestion(question) {
  const res = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

// ── Subcomponents ────────────────────────────────────────────────────────────

function UploadZone({ onUpload, uploading }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      style={{
        border: `1.5px dashed ${dragging ? "#7c3aed" : "#d1d5db"}`,
        borderRadius: 12,
        padding: "24px 16px",
        textAlign: "center",
        cursor: "pointer",
        background: dragging ? "#f5f3ff" : "transparent",
        transition: "all 0.2s",
        marginBottom: 16,
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.md"
        style={{ display: "none" }}
        onChange={(e) => onUpload(e.target.files[0])}
      />
      <div style={{ fontSize: 28, marginBottom: 8 }}>📄</div>
      <p style={{ margin: 0, fontSize: 13, color: "#6b7280" }}>
        {uploading ? "Uploading & indexing…" : "Drop PDF / TXT / MD or click to browse"}
      </p>
    </div>
  );
}

function DocItem({ doc, onDelete }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "8px 12px", borderRadius: 8, background: "#f9fafb",
      border: "0.5px solid #e5e7eb", marginBottom: 6, fontSize: 13,
    }}>
      <div>
        <div style={{ fontWeight: 500, color: "#111827" }}>{doc.filename}</div>
        <div style={{ color: "#9ca3af", fontSize: 12 }}>{doc.total_chunks} chunks</div>
      </div>
      <button
        onClick={() => onDelete(doc.doc_id)}
        style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", fontSize: 16 }}
        title="Remove document"
      >×</button>
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === ROLES.USER;
  return (
    <div style={{
      display: "flex", justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 12,
    }}>
      <div style={{
        maxWidth: "75%",
        padding: "10px 14px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser ? "#7c3aed" : "#f3f4f6",
        color: isUser ? "#fff" : "#111827",
        fontSize: 14, lineHeight: 1.6,
      }}>
        {msg.content}
        {msg.sources && msg.sources.length > 0 && (
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid rgba(0,0,0,0.1)" }}>
            <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 4 }}>Sources</div>
            {msg.sources.map((s, i) => (
              <div key={i} style={{ fontSize: 11, opacity: 0.8 }}>
                📎 {s.filename} · chunk {s.chunk_index} · score {s.score}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [messages, setMessages] = useState([
    { role: ROLES.BOT, content: "Hi! Upload a document and ask me anything about it." },
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef();

  useEffect(() => {
    fetchDocuments().then(setDocs).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const handleUpload = async (file) => {
    setUploading(true);
    setUploadStatus(null);
    try {
      const result = await uploadFile(file);
      setUploadStatus({ type: "success", text: `✓ ${result.filename} — ${result.chunks_created} chunks indexed` });
      const updated = await fetchDocuments();
      setDocs(updated);
    } catch (e) {
      setUploadStatus({ type: "error", text: `✗ ${e.message}` });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    await deleteDocument(docId);
    setDocs(docs.filter((d) => d.doc_id !== docId));
  };

  const handleSend = async () => {
    const q = input.trim();
    if (!q || thinking) return;
    setInput("");
    setMessages((m) => [...m, { role: ROLES.USER, content: q }]);
    setThinking(true);
    try {
      const result = await askQuestion(q);
      setMessages((m) => [...m, { role: ROLES.BOT, content: result.answer, sources: result.sources }]);
    } catch {
      setMessages((m) => [...m, { role: ROLES.BOT, content: "Something went wrong. Is the backend running?" }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter', sans-serif", background: "#fff" }}>
      {/* Sidebar */}
      <div style={{
        width: 280, borderRight: "1px solid #e5e7eb", padding: 20,
        display: "flex", flexDirection: "column", background: "#fafafa",
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#7c3aed", marginBottom: 4 }}>DocuMindAI</div>
        <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 20 }}>RAG Document Intelligence</div>

        <UploadZone onUpload={handleUpload} uploading={uploading} />

        {uploadStatus && (
          <div style={{
            fontSize: 12, padding: "8px 12px", borderRadius: 8, marginBottom: 12,
            background: uploadStatus.type === "success" ? "#f0fdf4" : "#fef2f2",
            color: uploadStatus.type === "success" ? "#16a34a" : "#dc2626",
            border: `0.5px solid ${uploadStatus.type === "success" ? "#bbf7d0" : "#fecaca"}`,
          }}>
            {uploadStatus.text}
          </div>
        )}

        <div style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Documents ({docs.length})
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          {docs.length === 0
            ? <div style={{ fontSize: 13, color: "#d1d5db", textAlign: "center", marginTop: 16 }}>No documents yet</div>
            : docs.map((d) => <DocItem key={d.doc_id} doc={d} onDelete={handleDelete} />)
          }
        </div>
      </div>

      {/* Chat panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 32px" }}>
          {messages.map((m, i) => <Message key={i} msg={m} />)}
          {thinking && (
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
              <div style={{ padding: "10px 14px", borderRadius: "16px 16px 16px 4px", background: "#f3f4f6", fontSize: 14 }}>
                <span style={{ animation: "pulse 1s infinite" }}>Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div style={{
          padding: "16px 24px", borderTop: "1px solid #e5e7eb",
          display: "flex", gap: 10,
        }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask anything about your documents…"
            style={{
              flex: 1, padding: "10px 16px", borderRadius: 10,
              border: "1px solid #e5e7eb", fontSize: 14, outline: "none",
            }}
          />
          <button
            onClick={handleSend}
            disabled={thinking}
            style={{
              padding: "10px 20px", borderRadius: 10,
              background: thinking ? "#ddd" : "#7c3aed", color: "#fff",
              border: "none", cursor: thinking ? "default" : "pointer",
              fontWeight: 600, fontSize: 14,
            }}
          >
            Ask →
          </button>
        </div>
      </div>
    </div>
  );
}
