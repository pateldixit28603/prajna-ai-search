export type Source = {
  id: string;
  n: number;
  title: string;
  url: string;
  domain: string;
  snippet: string;
  source: string;
  published?: string | null;
  authors: string[];
  extra: Record<string, unknown>;
};

export type Turn = {
  question: string;
  answer: string;
  sources: Source[];
  followups: string[];
  queries: string[];
  status: string;
  stage: "planning" | "reading" | "writing" | "done" | "error";
  warnings: string[];
  meta?: { total?: number; ttft?: number; nvidia?: boolean; timings?: Record<string, number> };
  error?: string;
};

export type ThreadSummary = { id: string; title: string; focus: string; updated_at: number };

export type Health = {
  status: string;
  nvidia: boolean;
  models: Record<string, string>;
  local_index: { chunks: number; documents: number; dense: boolean } | null;
  focus_modes: Record<string, string>;
};

const BASE = import.meta.env.VITE_API_URL ?? "";

export async function getHealth(): Promise<Health> {
  return (await fetch(`${BASE}/api/health`)).json();
}

export async function listThreads(): Promise<ThreadSummary[]> {
  return (await fetch(`${BASE}/api/threads`)).json();
}

export async function getThread(id: string) {
  const r = await fetch(`${BASE}/api/threads/${id}`);
  if (!r.ok) throw new Error("not found");
  return r.json();
}

export async function deleteThread(id: string) {
  await fetch(`${BASE}/api/threads/${id}`, { method: "DELETE" });
}

/** POST /api/search and parse the Server-Sent-Events stream. */
export async function streamSearch(
  body: { query: string; focus: string; thread_id?: string | null },
  onEvent: (e: any) => void,
  signal?: AbortSignal,
) {
  const res = await fetch(`${BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    const msg = res.status === 429 ? "Too many searches — wait a moment." : `Server error (${res.status})`;
    onEvent({ type: "error", message: msg });
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n\n")) !== -1) {
      const block = buf.slice(0, i);
      buf = buf.slice(i + 2);
      for (const line of block.split("\n")) {
        if (line.startsWith("data:")) {
          try {
            onEvent(JSON.parse(line.slice(5).trim()));
          } catch {
            /* ignore partial */
          }
        }
      }
    }
  }
}
