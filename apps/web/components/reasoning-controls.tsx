"use client";

import { useState } from "react";
import { runReasoningFromBrowser, type ReasoningResponse } from "../lib/api";

export function ReasoningControls() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ReasoningResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runReasoning() {
    setIsRunning(true);
    setError(null);
    try {
      const response = await runReasoningFromBrowser();
      setResult(response);
    } catch (reasoningError) {
      setError(reasoningError instanceof Error ? reasoningError.message : "Không chạy được reasoning.");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="control-panel">
      <button className="primary-button" type="button" onClick={runReasoning} disabled={isRunning}>
        {isRunning ? "Đang chạy..." : "Chạy suy luận"}
      </button>
      <button className="secondary-button" type="button" onClick={() => window.location.reload()}>
        Làm mới dashboard
      </button>

      {error ? <p className="error-text">{error}</p> : null}
      {result ? (
        <div className="result-box">
          <strong>Run {result.status}</strong>
          <span>{result.findings.length} finding</span>
          <span>{result.created_tasks.length} task</span>
          <span>{result.created_purchase_requests.length} purchase request</span>
        </div>
      ) : null}
    </div>
  );
}

