import { AlertTriangle, Check, Copy, CornerDownRight, GraduationCap, Languages, Layers, Loader2, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import { translateAnswer, type Turn } from "../lib/api";
import { LANGS, langDir, langName } from "../lib/langs";
import Answer from "./Answer";
import ResearchPanel from "./ResearchPanel";
import Sources, { SourceList, SourceSkeleton } from "./Sources";

const STEPS = [
  { id: "planning", label: "Plan" },
  { id: "reading", label: "Search & rank" },
  { id: "writing", label: "Write" },
];

function Steps({ stage, status }: { stage: Turn["stage"]; status: string }) {
  const idx = STEPS.findIndex((s) => s.id === stage);
  return (
    <div className="flex items-center gap-3 text-xs text-muted">
      {STEPS.map((s, i) => (
        <span key={s.id} className={`flex items-center gap-1.5 ${i <= idx ? "text-text" : ""}`}>
          {i < idx ? <Check size={12} className="text-nv" /> : i === idx ? <Loader2 size={12} className="animate-spin text-nv" /> : <span className="h-1.5 w-1.5 rounded-full bg-line" />}
          {s.label}
        </span>
      ))}
      <span className="hidden truncate sm:inline">· {status}</span>
    </div>
  );
}

/** One-click answer language switch: re-rendered by the NIM LLM, same sources, same [n] citations. */
function LangBar({ turn, threadId, onLang }: {
  turn: Turn; threadId: string | null; onLang: (code: string, text?: string) => void;
}) {
  const [pending, setPending] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const original = turn.lang ?? "en";
  const shown = turn.shownLang ?? original;

  const pick = async (code: string) => {
    if (pending || code === shown) return;
    setNote("");
    if (code === original || turn.translations?.[code]) {
      onLang(code);
      if (turn.turnId != null) translateAnswer({ text: turn.answer, lang: code, n_sources: turn.sources.length, turn_id: turn.turnId, thread_id: threadId }).catch(() => {});
      return;
    }
    setPending(code);
    try {
      const r = await translateAnswer({
        text: turn.answer, lang: code, n_sources: turn.sources.length, turn_id: turn.turnId, thread_id: threadId,
      });
      if (r.ok) onLang(code, r.text);
      else setNote(r.message || "Translation unavailable right now.");
    } catch (e) {
      setNote((e as Error).message);
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="mt-5">
      <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Answer language">
        <Languages size={14} className="me-1 text-muted" />
        {LANGS.map((l) => (
          <button
            key={l.code}
            onClick={() => pick(l.code)}
            disabled={!!pending}
            aria-pressed={shown === l.code}
            title={l.code === original ? `${l.label} (original)` : `Show this answer in ${l.label}`}
            className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition disabled:cursor-wait ${
              shown === l.code ? "border-nv/70 bg-nv-soft text-nv" : "border-line text-muted hover:border-nv/50 hover:text-text"
            }`}
          >
            {pending === l.code && <Loader2 size={11} className="animate-spin" />}
            <span>{l.label}</span>
          </button>
        ))}
      </div>
      {shown !== original && (
        <p className="mt-2 text-xs text-muted">
          Translated from {langName(original)} by NVIDIA NIM · same sources, every [n] citation kept ·{" "}
          <button className="underline underline-offset-2 hover:text-text" onClick={() => pick(original)}>show original</button>
        </p>
      )}
      {note && <p className="mt-2 text-xs text-amber-300/90">{note}</p>}
    </div>
  );
}

export default function TurnView({ turn, onFollowup, live, threadId, onLang }: {
  turn: Turn; onFollowup: (q: string) => void; live: boolean;
  threadId: string | null; onLang: (code: string, text?: string) => void;
}) {
  const [tab, setTab] = useState<"answer" | "sources" | "research">("answer");
  const [copied, setCopied] = useState(false);
  const streaming = live && turn.stage === "writing";
  const done = turn.stage === "done";
  const shown = turn.shownLang ?? turn.lang;
  const text = (shown && shown !== turn.lang && turn.translations?.[shown]) || turn.answer;
  const dir = langDir(shown && turn.translations?.[shown] ? shown : turn.lang);

  const copy = async () => {
    const refs = turn.sources.map((s) => `[${s.n}] ${s.title} — ${s.url}`).join("\n");
    await navigator.clipboard.writeText(`${text}\n\nSources:\n${refs}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article className="border-b border-line pb-10">
      <h2 dir="auto" className="font-display text-[1.7rem] leading-tight font-semibold tracking-tight md:text-3xl">{turn.question}</h2>

      <div className="mt-4 flex items-center gap-5 border-b border-line text-sm">
        {(["answer", "sources", "research"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px flex items-center gap-1.5 border-b-2 pb-2.5 capitalize transition ${
              tab === t ? "border-nv text-text" : "border-transparent text-muted hover:text-text"
            }`}
          >
            {t === "answer" ? <Sparkles size={14} /> : t === "sources" ? <Layers size={14} /> : <GraduationCap size={14} />}
            {t}
            {t === "sources" && turn.sources.length > 0 && <span className="font-mono text-xs text-muted">{turn.sources.length}</span>}
          </button>
        ))}
        {!done && turn.stage !== "error" && (
          <div className="ml-auto pb-2.5">
            <Steps stage={turn.stage} status={turn.status} />
          </div>
        )}
      </div>

      {tab === "research" ? (
        <ResearchPanel query={turn.queries[0] || turn.question} />
      ) : tab === "sources" ? (
        <div className="mt-5">
          <SourceList sources={turn.sources} />
        </div>
      ) : (
        <>
          {turn.queries.length > 0 && (
            <p className="mt-4 flex flex-wrap items-center gap-1.5 text-xs text-muted">
              Searched:
              {turn.queries.map((q) => (
                <span key={q} className="rounded-md bg-panel px-2 py-0.5 font-mono">{q}</span>
              ))}
            </p>
          )}
          <div className="mt-4">
            {turn.sources.length ? <Sources sources={turn.sources} /> : turn.stage !== "done" && turn.stage !== "error" ? <SourceSkeleton /> : null}
          </div>

          <div className="mt-6">
            {turn.answer ? (
              <Answer text={text} sources={turn.sources} streaming={streaming} dir={dir} evidence={done ? turn.evidence : undefined} />
            ) : turn.stage !== "error" ? (
              <div className="space-y-2.5">
                <div className="shimmer h-4 w-11/12 rounded" />
                <div className="shimmer h-4 w-full rounded" />
                <div className="shimmer h-4 w-3/4 rounded" />
              </div>
            ) : null}
          </div>

          {turn.error && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300">
              <AlertTriangle size={16} /> {turn.error}
            </div>
          )}

          {done && turn.answer && <LangBar turn={turn} threadId={threadId} onLang={onLang} />}

          {done && (
            <div className="mt-5 flex flex-wrap items-center gap-3 text-xs text-muted">
              <button onClick={copy} className="flex items-center gap-1.5 rounded-lg px-2 py-1 hover:bg-panel hover:text-text">
                {copied ? <Check size={13} className="text-nv" /> : <Copy size={13} />} {copied ? "Copied" : "Copy"}
              </button>
              {turn.meta?.total != null && (
                <span className="flex items-center gap-1">
                  <Zap size={12} className={turn.meta.nvidia ? "text-nv" : ""} />
                  {turn.meta.total.toFixed(1)}s{turn.meta.nvidia ? " · NVIDIA NIM" : " · extractive"}
                  {turn.meta.timings?.rerank ? " · reranked" : ""}
                </span>
              )}
              {turn.warnings.length > 0 && <span title={turn.warnings.join(", ")}>· {turn.warnings.length} source(s) unavailable</span>}
            </div>
          )}

          {done && turn.followups.length > 0 && (
            <div className="mt-7">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-medium"><Layers size={15} className="text-nv" /> Related</h3>
              <ul className="divide-y divide-line border-y border-line">
                {turn.followups.map((f) => (
                  <li key={f}>
                    <button dir="auto" onClick={() => onFollowup(f)} className="flex w-full items-center gap-3 py-3 text-left text-[15px] text-text/90 transition hover:text-nv">
                      <CornerDownRight size={15} className="shrink-0 text-muted" /> {f}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </article>
  );
}
