import {
  AlertTriangle, CheckCircle2, ChevronDown, CircleHelp, ExternalLink, Loader2, Scale, ShieldCheck, XCircle, Zap,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { factCheck, type FactCheckResult, type FactEvidence } from "../lib/api";

export type CheckItem = { id: string; claim: string; status: "pending" | "done" | "error"; result?: FactCheckResult; error?: string };

const EXAMPLES = [
  "The Great Wall of China is visible from space with the naked eye.",
  "Nvidia was founded in 1993 by Jensen Huang, Chris Malachowsky and Curtis Priem.",
  "Humans only use 10 percent of their brains.",
  "The Transformer architecture was introduced in the paper \"Attention Is All You Need\".",
];

const FOCUS = [
  { id: "all", label: "All sources" },
  { id: "wiki", label: "Encyclopedia" },
  { id: "academic", label: "Academic" },
  { id: "tech", label: "Tech news" },
];

const VERDICT_STYLE: Record<FactCheckResult["verdict"], { cls: string; icon: typeof CheckCircle2; blurb: string }> = {
  supported: { cls: "border-nv/60 bg-nv/10 text-nv", icon: CheckCircle2, blurb: "The sources back this claim." },
  contradicted: { cls: "border-red-500/60 bg-red-500/10 text-red-300", icon: XCircle, blurb: "The sources say otherwise." },
  disputed: { cls: "border-amber-500/60 bg-amber-500/10 text-amber-300", icon: Scale, blurb: "Sources disagree. Read both sides." },
  not_enough_evidence: { cls: "border-line bg-panel-2 text-text/80", icon: CircleHelp, blurb: "The open sources don't settle this claim." },
  unverified: { cls: "border-line bg-panel-2 text-text/80", icon: AlertTriangle, blurb: "The claim could not be judged right now." },
};

const STANCE_LABEL: Record<string, string> = {
  supports: "Supports", contradicts: "Contradicts", neutral: "Not decisive", unknown: "Not judged",
};
const STANCE_CLS: Record<string, string> = {
  supports: "border-nv/40 text-nv", contradicts: "border-red-500/50 text-red-300",
  neutral: "border-line text-muted", unknown: "border-line text-muted",
};

const short = (m: string | null) => (m ? m.split("/").pop()!.replace("nemotron-3.5-", "Nemotron ").replace(/-/g, " ") : "");

/** Render "[n]" citations in the summary as small chips that jump to the evidence card. */
function withCites(text: string, id: string): ReactNode[] {
  return text.split(/(\[\d{1,2}\])/g).map((part, i) => {
    const m = part.match(/^\[(\d{1,2})\]$/);
    if (!m) return part;
    return (
      <a key={i} href={`#ev-${id}-${m[1]}`} onClick={(e) => { e.preventDefault(); document.getElementById(`ev-${id}-${m[1]}`)?.scrollIntoView({ behavior: "smooth", block: "center" }); }}
        className="mx-0.5 inline-grid h-[18px] min-w-[18px] place-items-center rounded bg-panel-2 px-1 align-[2px] font-mono text-[10px] text-nv hover:bg-nv hover:text-ink">
        {m[1]}
      </a>
    );
  });
}

function Passage({ e }: { e: FactEvidence }) {
  const [a, b] = e.highlight ?? [0, 0];
  return (
    <p dir="auto" className="text-[13px] leading-relaxed text-text/75">
      {e.cut_before && "… "}
      {e.highlight ? (
        <>
          {e.passage.slice(0, a)}
          <mark className="rounded bg-nv/20 px-0.5 text-text">{e.passage.slice(a, b)}</mark>
          {e.passage.slice(b)}
        </>
      ) : e.passage}
      {e.cut_after && " …"}
    </p>
  );
}

function EvidenceCard({ e, id }: { e: FactEvidence; id: string }) {
  return (
    <article id={`ev-${id}-${e.n}`} className="min-w-0 scroll-mt-24 rounded-xl border border-line bg-panel p-3.5">
      <header className="mb-2 flex items-start gap-2">
        <span className="mt-0.5 grid h-5 min-w-5 place-items-center rounded bg-panel-2 px-1 font-mono text-[10px] text-nv">{e.n}</span>
        <a href={e.url} target="_blank" rel="noreferrer" className="group min-w-0 flex-1">
          <span className="flex items-center gap-1 text-sm font-medium group-hover:text-nv">
            <span className="truncate">{e.title}</span> <ExternalLink size={12} className="shrink-0 opacity-60" />
          </span>
          <span className="block truncate text-[11px] text-muted">
            {e.domain}{e.published ? ` · ${e.published}` : ""}
          </span>
        </a>
        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${STANCE_CLS[e.stance]}`}>{STANCE_LABEL[e.stance]}</span>
      </header>
      {e.reason && <p dir="auto" className="mb-2 text-[13px] text-text/90">{e.reason}</p>}
      <Passage e={e} />
      {e.score !== null && (
        <p className="mt-2 font-mono text-[10px] text-muted" title="Relevance score from NVIDIA Rerank 8B (or hybrid search when the reranker is unavailable)">
          relevance {e.score.toFixed(2)}
        </p>
      )}
    </article>
  );
}

function Meter({ r }: { r: FactCheckResult }) {
  const { supports: s, contradicts: c, neutral: n } = r.counts;
  const total = Math.max(1, s + c + n);
  return (
    <div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-panel-2" role="img"
        aria-label={`${s} passages support, ${c} contradict, ${n} are not decisive`}>
        <span className="bg-nv" style={{ width: `${(s / total) * 100}%` }} />
        <span className="bg-red-500" style={{ width: `${(c / total) * 100}%` }} />
        <span className="bg-line" style={{ width: `${(n / total) * 100}%` }} />
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted">
        <span><b className="text-nv">{s}</b> support</span>
        <span><b className="text-red-300">{c}</b> contradict</span>
        <span><b className="text-text/80">{n}</b> not decisive</span>
        {r.agreement !== null && <span className="ms-auto">source agreement {Math.round(r.agreement * 100)}%</span>}
      </div>
    </div>
  );
}

function Group({ title, items, id, open: initial }: { title: string; items: FactEvidence[]; id: string; open: boolean }) {
  const [open, setOpen] = useState(initial);
  if (!items.length) return null;
  return (
    <section>
      <button onClick={() => setOpen(!open)} aria-expanded={open}
        className="mb-2 flex w-full items-center gap-2 text-left text-xs font-medium tracking-wider text-muted uppercase hover:text-text">
        <ChevronDown size={14} className={`transition ${open ? "" : "-rotate-90"}`} /> {title} <span className="font-mono">({items.length})</span>
      </button>
      {open && <div className="grid grid-cols-1 gap-2.5 md:grid-cols-2">{items.map((e) => <EvidenceCard key={e.n} e={e} id={id} />)}</div>}
    </section>
  );
}

function ResultView({ item }: { item: CheckItem }) {
  if (item.status === "pending") {
    return (
      <div className="rounded-2xl border border-line bg-panel p-5">
        <p dir="auto" className="font-display text-lg">“{item.claim}”</p>
        <p className="mt-3 flex items-center gap-2 text-sm text-muted">
          <Loader2 size={15} className="animate-spin text-nv" /> Searching open sources, reranking passages and weighing the evidence…
        </p>
        <div className="shimmer mt-4 h-2.5 rounded-full" />
      </div>
    );
  }
  if (item.status === "error" || !item.result) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-950/20 p-5 text-sm text-red-300">
        <p dir="auto" className="mb-1 text-text/90">“{item.claim}”</p>
        <span className="flex items-center gap-2"><AlertTriangle size={15} /> {item.error}</span>
      </div>
    );
  }
  const r = item.result;
  const v = VERDICT_STYLE[r.verdict];
  const Icon = v.icon;
  const by = (st: string) => r.evidence.filter((e) => e.stance === st);
  const judged = r.evidence.some((e) => e.stance !== "unknown");
  return (
    <div className="space-y-5 rounded-2xl border border-line bg-panel/60 p-4 md:p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start">
        <div className={`flex shrink-0 items-center gap-2.5 rounded-xl border px-3.5 py-2.5 ${v.cls}`}>
          <Icon size={22} />
          <span>
            <span className="block text-base leading-tight font-semibold">{r.label}</span>
            {r.confidence !== "none" && <span className="block text-[11px] opacity-80">{r.confidence} confidence</span>}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p dir="auto" className="font-display text-lg leading-snug">“{r.claim}”</p>
          <p className="mt-1 text-xs text-muted">{v.blurb}</p>
        </div>
      </div>

      {judged && <Meter r={r} />}

      {r.summary && <p dir="auto" className="text-[15px] leading-relaxed text-text/90">{withCites(r.summary, item.id)}</p>}

      <div className="space-y-4">
        <Group title="Evidence for" items={by("supports")} id={item.id} open />
        <Group title="Evidence against" items={by("contradicts")} id={item.id} open />
        <Group title="Related, not decisive" items={by("neutral")} id={item.id} open={!by("supports").length && !by("contradicts").length} />
        <Group title="Most relevant passages" items={by("unknown")} id={item.id} open />
      </div>

      <footer className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-line pt-3 text-[11px] text-muted">
        <span className="flex items-center gap-1"><Zap size={11} className="text-nv" /> {r.timings.total?.toFixed(1)}s</span>
        {r.models.plan && <span><b className="font-medium text-text/80">{short(r.models.plan)}</b> planned {r.queries.length} {r.queries.length === 1 ? "query" : "queries"}</span>}
        <span>{r.sources} sources read</span>
        {r.models.rerank && <span><b className="font-medium text-text/80">Rerank 8B</b> picked {r.evidence.length} passages</span>}
        {r.models.judge && <span><b className="font-medium text-text/80">{short(r.models.judge)}</b> judged each passage</span>}
        <span className="w-full text-[10px] md:ms-auto md:w-auto">The verdict is counted from the passage labels, not written by the model.</span>
      </footer>
    </div>
  );
}

export default function FactCheck({ nvidia, items, setItems }: {
  nvidia: boolean | null; items: CheckItem[]; setItems: (fn: (xs: CheckItem[]) => CheckItem[]) => void;
}) {
  const [claim, setClaim] = useState("");
  const [focus, setFocus] = useState("all");
  const busy = items.some((x) => x.status === "pending");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(Math.max(el.scrollHeight, 76), 200) + "px";
  }, [claim]);

  const run = async (text = claim) => {
    const v = text.trim();
    if (v.length < 3 || busy) return;
    const id = `${Date.now()}`;
    setItems((xs) => [{ id, claim: v, status: "pending" }, ...xs]);
    setClaim("");
    const patch = (p: Partial<CheckItem>) => setItems((xs) => xs.map((x) => (x.id === id ? { ...x, ...p } : x)));
    try {
      patch({ status: "done", result: await factCheck({ claim: v, focus }) });
    } catch (err) {
      patch({ status: "error", error: (err as Error).message || "Fact-check failed." });
    }
  };

  return (
    <div className="scroll-thin flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-4 pt-10 pb-24 md:px-8 md:pt-14">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-nv/40 bg-nv-soft px-3 py-1 text-xs font-medium text-nv">
            <ShieldCheck size={12} /> Fact-check · NVIDIA Rerank + Nemotron
          </span>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-tight md:text-5xl">
            Heard it somewhere? <span className="text-nv">Check it.</span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm text-muted md:text-base">
            Paste a claim. Prajna finds the most relevant passages in open sources, labels each one as for or against,
            and shows you the verdict with the evidence on both sides.
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-3xl rounded-2xl border border-line bg-panel p-2 glow focus-within:border-nv/70">
          <textarea ref={ref} value={claim} onChange={(e) => setClaim(e.target.value)} maxLength={500}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); run(); } }}
            placeholder="e.g. The Great Wall of China is visible from space with the naked eye."
            aria-label="Claim to fact-check"
            className="w-full resize-none bg-transparent px-3.5 pt-3 pb-2 text-[1.05rem] outline-none placeholder:text-muted" />
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line px-2 pt-2.5 pb-1.5">
            <div className="scroll-thin -mx-1 flex gap-1.5 overflow-x-auto px-1" role="group" aria-label="Sources to check">
              {FOCUS.map((f) => (
                <button key={f.id} onClick={() => setFocus(f.id)} aria-pressed={focus === f.id}
                  className={`shrink-0 rounded-full border px-3 py-1 text-xs transition ${
                    focus === f.id ? "border-nv/70 bg-nv-soft text-nv" : "border-line text-muted hover:border-nv/40 hover:text-text"
                  }`}>
                  {f.label}
                </button>
              ))}
            </div>
            <button onClick={() => run()} disabled={busy || claim.trim().length < 3}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-nv px-4 py-2 text-sm font-semibold text-ink transition hover:brightness-110 disabled:bg-panel-2 disabled:text-muted sm:w-auto">
              {busy ? <Loader2 size={15} className="animate-spin" /> : <ShieldCheck size={15} />}
              {busy ? "Checking…" : "Check claim"}
            </button>
          </div>
        </div>
        {nvidia === false && (
          <p className="mx-auto mt-3 max-w-3xl text-center text-xs text-amber-400">
            NVIDIA NIM is not configured here, so Prajna can show the evidence but not judge it.
          </p>
        )}

        {items.length === 0 ? (
          <div className="mx-auto mt-6 grid max-w-3xl gap-2 sm:grid-cols-2">
            {EXAMPLES.map((q) => (
              <button key={q} onClick={() => run(q)}
                className="group flex items-start gap-3 rounded-xl border border-line bg-panel/40 px-3.5 py-3 text-left transition hover:border-nv/60 hover:bg-panel">
                <ShieldCheck size={16} className="mt-0.5 shrink-0 text-muted group-hover:text-nv" />
                <span className="text-[13px] text-text/85 group-hover:text-text">{q}</span>
              </button>
            ))}
          </div>
        ) : (
          <div className="mx-auto mt-8 max-w-3xl space-y-6">
            {items.map((it) => <ResultView key={it.id} item={it} />)}
          </div>
        )}
      </div>
    </div>
  );
}
