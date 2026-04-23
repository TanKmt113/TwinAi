"use client";

import { useState } from "react";
import {
  parseManualFromBrowser,
  queryChatFromBrowser,
  uploadManualFromBrowser,
  type ChatResponse,
  type Manual,
  type ManualChunk,
} from "../lib/api";

type ManualChatPanelProps = {
  manuals: Manual[];
};

/** Maps API `agent_mode` to a short label so operators see whether Gemini/OpenAI was invoked. */
function describeLlmUsage(agentMode: string | undefined): { headline: string; detail: string } {
  if (!agentMode) {
    return { headline: "Chưa rõ", detail: "Thiếu agent_mode từ API." };
  }
  if (agentMode.startsWith("llm_tool_agent:")) {
    const provider = agentMode.slice("llm_tool_agent:".length);
    return {
      headline: `LLM đang bật (${provider})`,
      detail: "Kết luận được tạo qua LLM trên TOOL_CONTEXT (Gemini/OpenAI).",
    };
  }
  if (agentMode === "rule_fallback_no_llm_key") {
    return {
      headline: "Không gọi LLM",
      detail: "Thiếu API key hoặc provider chưa cấu hình — chỉ rule/template.",
    };
  }
  if (agentMode === "rule_fallback_after_llm_error") {
    return {
      headline: "LLM lỗi — fallback rule",
      detail: "Gọi LLM thất bại; hệ thống dùng rule fallback.",
    };
  }
  if (agentMode === "guardrail_out_of_scope") {
    return {
      headline: "Không gọi LLM (guardrail)",
      detail: "Câu hỏi ngoài phạm vi ontology — không gọi model.",
    };
  }
  return { headline: "Chế độ khác", detail: agentMode };
}

export function ManualChatPanel({ manuals }: ManualChatPanelProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedManual, setUploadedManual] = useState<Manual | null>(null);
  const [chunks, setChunks] = useState<ManualChunk[]>([]);
  const [question, setQuestion] = useState("Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [isWorking, setIsWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeManual = uploadedManual ?? manuals[0];

  async function uploadManual() {
    if (!selectedFile) {
      setError("Vui lòng chọn file manual trước.");
      return;
    }
    setIsWorking(true);
    setError(null);
    try {
      const manual = await uploadManualFromBrowser(selectedFile);
      setUploadedManual(manual);
      setChunks([]);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Không upload được manual.");
    } finally {
      setIsWorking(false);
    }
  }

  async function parseManual() {
    if (!activeManual) {
      setError("Chưa có manual để parse.");
      return;
    }
    setIsWorking(true);
    setError(null);
    try {
      const parsedChunks = await parseManualFromBrowser(activeManual.id);
      setChunks(parsedChunks);
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : "Không parse được manual.");
    } finally {
      setIsWorking(false);
    }
  }

  async function askQuestion() {
    setIsWorking(true);
    setError(null);
    try {
      const response = await queryChatFromBrowser(question);
      setAnswer(response);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "Không truy vấn được chat.");
    } finally {
      setIsWorking(false);
    }
  }

  return (
    <div className="phase4-grid">
      <div className="manual-box">
        <p className="eyebrow">Manual</p>
        <h2>Upload & Parse</h2>
        <div className="form-stack">
          <input
            type="file"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            accept=".txt,.md,.csv,.pdf,.doc,.docx"
          />
          <div className="button-row">
            <button className="primary-button" type="button" onClick={uploadManual} disabled={isWorking}>
              Upload
            </button>
            <button className="secondary-button" type="button" onClick={parseManual} disabled={isWorking || !activeManual}>
              Parse manual
            </button>
          </div>
        </div>
        <div className="list-stack compact">
          {manuals.slice(0, 4).map((manual) => (
            <div className="list-item vertical" key={manual.id}>
              <strong>{manual.code}</strong>
              <span>{manual.title} · {manual.status}</span>
            </div>
          ))}
          {uploadedManual ? (
            <div className="list-item vertical">
              <strong>{uploadedManual.code}</strong>
              <span>{uploadedManual.title} · uploaded</span>
            </div>
          ) : null}
        </div>
        {chunks.length ? (
          <div className="list-stack compact">
            <p className="muted">{chunks.length} chunk đã parse trong phiên này.</p>
            {chunks.slice(0, 3).map((chunk) => (
              <div className="list-item vertical" key={chunk.id}>
                <strong>Chunk {chunk.chunk_index}</strong>
                <span>{chunk.chunk_text.slice(0, 180)}...</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="chat-box">
        <p className="eyebrow">Chat / RAG</p>
        <h2>Hỏi Ontology</h2>
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} />
        <div className="button-row">
          <button className="primary-button" type="button" onClick={askQuestion} disabled={isWorking}>
            Truy vấn
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setQuestion("Dự báo doanh thu tháng sau là bao nhiêu?")}
          >
            Test ngoài phạm vi
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
        {answer ? <ChatAnswer answer={answer} /> : <p className="empty-text">Chưa có câu trả lời.</p>}
      </div>
    </div>
  );
}

function ChatAnswer({ answer }: { answer: ChatResponse }) {
  const toolCalls = answer.tool_calls ?? [];
  const llm = describeLlmUsage(answer.agent_mode);
  const llmOk = answer.agent_mode?.startsWith("llm_tool_agent:") ?? false;

  return (
    <div className="chat-answer">
      <div className={`chat-llm-status${llmOk ? " chat-llm-status--ok" : ""}`}>
        <strong>{llm.headline}</strong>
        <span>{llm.detail}</span>
      </div>
      <strong>{answer.conclusion}</strong>
      <span>Intent: {answer.intent}</span>
      <span className="chat-agent-raw">agent_mode: {answer.agent_mode ?? "unknown"}</span>
      <div>
        <p className="mini-heading">Tool calls</p>
        <ul>
          {toolCalls.map((tool) => (
            <li key={tool}>{tool}</li>
          ))}
          {!toolCalls.length ? <li>Không có tool call.</li> : null}
        </ul>
      </div>
      <div>
        <p className="mini-heading">Evidence</p>
        <ul>
          {answer.evidence.map((item) => (
            <li key={item}>{item}</li>
          ))}
          {!answer.evidence.length ? <li>Không có evidence.</li> : null}
        </ul>
      </div>
      <div>
        <p className="mini-heading">Recommended actions</p>
        <ul>
          {answer.recommended_actions.map((item) => (
            <li key={item}>{item}</li>
          ))}
          {!answer.recommended_actions.length ? <li>Không có hành động đề xuất.</li> : null}
        </ul>
      </div>
      <div>
        <p className="mini-heading">Missing data</p>
        <ul>
          {answer.missing_data.map((item) => (
            <li key={item}>{item}</li>
          ))}
          {!answer.missing_data.length ? <li>Không thiếu dữ liệu quan trọng.</li> : null}
        </ul>
      </div>
      <div>
        <p className="mini-heading">Citations</p>
        <ul>
          {answer.citations.map((citation) => (
            <li key={`${citation.type}-${citation.code}`}>
              {citation.type}: {citation.code} - {citation.title}
            </li>
          ))}
          {!answer.citations.length ? <li>Không có citation.</li> : null}
        </ul>
      </div>
    </div>
  );
}
