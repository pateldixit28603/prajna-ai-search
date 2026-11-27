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

/** The passage behind one [n] citation: the k-th occurrence of [n] in the answer. */
export type Evidence = {
  n: number; k: number; claim: string; passage: string; highlight: [number, number] | null;
  overlap: number; matched: string[]; cut_before: boolean; cut_after: boolean;
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
  meta?: { total?: number; ttft?: number; nvidia?: boolean; timings?: Record<string, number>; lang?: string };
  error?: string;
  /** language the answer was written in (detected from the question, or chosen) */
  lang?: string;
  /** stored turn id, used to cache translations server-side */
  turnId?: number;
  /** answer re-rendered in other languages, keyed by language code */
  translations?: Record<string, string>;
  /** language currently shown for this answer */
  shownLang?: string;
  /** supporting passage for each citation, from the retrieved (NVIDIA-reranked) passages */
  evidence?: Evidence[];
  /** "image" turns hold a generated picture instead of an answer */
  kind?: "answer" | "image";
  image?: ImageResult;
};

export type ImageResult = {
  image: string; model: string; seed: number; aspect: string; prompt: string; enhanced: boolean; total: number;
  thread_id?: string; turn_id?: number;
};

export type Paper = {
  id: string; title: string; year: number | null; cited_by: number; authors: string[];
  venue: string | null; url: string; oa_url: string | null; abstract: string;
};

export type Research = {
  query: string; total_works: number; key_papers: Paper[]; foundational: Paper[]; rising: Paper[];
  read_next: Paper[]; timeline: { year: number; count: number }[]; peak_year: number | null; warnings: string[];
};

async function errorOf(r: Response) {
  try {
    const j = await r.json();
    if (j?.detail) return String(j.detail);
  } catch { /* not json */ }
  return r.status === 429 ? "Too many requests — wait a moment." : `Server error (${r.status})`;
}

/** Literature map for a topic (OpenAlex): key / foundational / rising papers, read-next, timeline. */
export async function getResearch(q: string): Promise<Research> {
  const r = await fetch(`${BASE}/api/research?q=${encodeURIComponent(q)}`);
  if (!r.ok) throw new Error(await errorOf(r));
  return r.json();
}

/** Generate an image with NVIDIA visual GenAI (FLUX / Stable Diffusion). */
export async function createImage(body: {
  prompt: string; aspect: string; enhance: boolean; seed?: number; thread_id?: string | null;
}): Promise<ImageResult> {
  const r = await fetch(`${BASE}/api/image`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await errorOf(r));
  return r.json();
}

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

export type TranslateResult = { lang: string; dir: "ltr" | "rtl"; text: string; ok: boolean; message: string; citations_ok: boolean };

/** Re-render an answer in another language with the NIM LLM (no new search; citations preserved). */
export async function translateAnswer(body: {
  text: string; lang: string; n_sources: number; turn_id?: number; thread_id?: string | null;
}): Promise<TranslateResult> {
  const r = await fetch(`${BASE}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(r.status === 429 ? "Too many requests — wait a moment." : `Server error (${r.status})`);
  return r.json();
}

/** POST /api/search and parse the Server-Sent-Events stream. */
export async function streamSearch(
  body: { query: string; focus: string; thread_id?: string | null; lang?: string | null },
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
