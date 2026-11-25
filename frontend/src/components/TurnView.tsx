import { AlertTriangle, Check, Copy, CornerDownRight, Layers, Loader2, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import type { Turn } from "../lib/api";
import Answer from "./Answer";
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

export default function TurnView({ turn, onFollowup, live }: { turn: Turn; onFollowup: (q: string) => void; live: boolean }) {
  const [tab, setTab] = useState<"answer" | "sources">("answer");
  const [copied, setCopied] = useState(false);
  const streaming = live && turn.stage === "writing";
  const done = turn.stage === "done";

  const copy = async () => {
    const refs = turn.sources.map((s) => `[${s.n}] ${s.title} — ${s.url}`).join("\n");
    await navigator.clipboard.writeText(`${turn.answer}\n\nSources:\n${refs}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article className="border-b border-line pb-10">
      <h2 className="font-display text-[1.7rem] leading-tight font-semibold tracking-tight md:text-3xl">{turn.question}</h2>

      <div className="mt-4 flex items-center gap-5 border-b border-line text-sm">
        {(["answer", "sources"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px flex items-center gap-1.5 border-b-2 pb-2.5 capitalize transition ${
              tab === t ? "border-nv text-text" : "border-transparent text-muted hover:text-text"
            }`}
          >
            {t === "answer" ? <Sparkles size={14} /> : <Layers size={14} />}
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

      {tab === "sources" ? (
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
              <Answer text={turn.answer} sources={turn.sources} streaming={streaming} />
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
                    <button onClick={() => onFollowup(f)} className="flex w-full items-center gap-3 py-3 text-left text-[15px] text-text/90 transition hover:text-nv">
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
