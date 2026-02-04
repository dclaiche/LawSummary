import type { CaseResponse, FinalResult } from "@/types";
import type { StreamEvent } from "@/types/events";

const BASE_URL = "/api";

export async function submitCase(text: string): Promise<CaseResponse> {
  const resp = await fetch(`${BASE_URL}/case`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function getCase(runId: string): Promise<FinalResult> {
  const resp = await fetch(`${BASE_URL}/case/${runId}`);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export function connectSSE(
  runId: string,
  onEvent: (event: StreamEvent) => void,
  onError: (error: Error) => void,
  onClose: () => void,
): () => void {
  const url = `${BASE_URL}/case/${runId}/stream`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (e) => {
    try {
      const event: StreamEvent = JSON.parse(e.data);
      onEvent(event);
    } catch (err) {
      onError(new Error(`Failed to parse SSE event: ${err}`));
    }
  };

  eventSource.onerror = () => {
    onError(new Error("SSE connection error"));
    eventSource.close();
    onClose();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
  };
}

export async function healthCheck(): Promise<boolean> {
  try {
    const resp = await fetch(`${BASE_URL}/health`);
    return resp.ok;
  } catch {
    return false;
  }
}
