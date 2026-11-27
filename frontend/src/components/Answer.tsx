import { ExternalLink, Quote, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Evidence, Source } from "../lib/api";

/** Turn "[3]" citations into markdown links "#cite-3-k", where k counts earlier [3]s (evidence key). */
function linkCitations(md: string) {
  const seen = new Map<string, number>();
  return md.replace(/\[(\d{1,2})\](?!\()/g, (_m, n: string) => {
    const k = seen.get(n) ?? 0;
    seen.set(n, k + 1);
    return `[${n}](#cite-${n}-${k})`;
  });
}

type Open = { key: string; rect: DOMRect; pinned: boolean };

const canHover = () => typeof window !== "undefined" && window.matchMedia?.("(hover: hover)").matches;

function EvidenceCard({ ev, source, rect, onClose, onEnter, onLeave }: {
  ev: Evidence; source: Source; rect: DOMRect; onClose: () => void; onEnter: () => void; onLeave: () => void;
}) {
  const width = Math.min(400, window.innerWidth - 16);
  const left = Math.max(8, Math.min(rect.left - 24, window.innerWidth - width - 8));
  const below = rect.bottom + 8;
  const placeAbove = below + 260 > window.innerHeight && rect.top > 300;
  const style: React.CSSProperties = placeAbove
    ? { left, width, bottom: window.innerHeight - rect.top + 8 }
    : { left, width, top: below };
  const [a, b] = ev.highlight ?? [0, 0];
  const pct = Math.round(ev.overlap * 100);
  return createPortal(
    <div
      role="dialog"
      aria-label={`Evidence for citation ${ev.n}`}
      style={style}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      className="evidence-card fixed z-50 rounded-xl border border-line bg-panel p-3.5 text-sm shadow-2xl shadow-black/60"
    >
      <div className="flex items-start gap-2">
        <span className="cite shrink-0">{ev.n}</span>
        <a href={source.url} target="_blank" rel="noreferrer" className="min-w-0 flex-1 font-medium leading-snug text-text hover:text-nv">
          <span className="line-clamp-2">{source.title}</span>
          <span className="mt-0.5 flex items-center gap-1 text-xs font-normal text-muted">{source.domain} <ExternalLink size={11} /></span>
        </a>
        <button onClick={onClose} aria-label="Close evidence" className="rounded p-0.5 text-muted hover:text-text"><X size={14} /></button>
      </div>
      <p dir="auto" className="mt-3 flex gap-1.5 text-xs text-muted">
        <Quote size={12} className="mt-0.5 shrink-0 text-nv" /> <span className="line-clamp-2">{ev.claim}</span>
      </p>
      <blockquote dir="auto" className="mt-2 max-h-56 overflow-y-auto border-s-2 border-nv/60 ps-3 text-[13.5px] leading-relaxed text-text/85">
        {ev.cut_before && "… "}
        {ev.highlight ? (
          <>
            {ev.passage.slice(0, a)}
            <mark className="evidence-mark">{ev.passage.slice(a, b)}</mark>
            {ev.passage.slice(b)}
          </>
        ) : ev.passage}
        {ev.cut_after && " …"}
      </blockquote>
      <p className="mt-2.5 text-[11px] text-muted">
        {ev.highlight
          ? `Exact passage Prajna read from this source · ${pct}% of the sentence's key words appear in the highlighted text`
          : "Closest passage Prajna read from this source · no shared key words (it may be in another language), so check the source"}
      </p>
    </div>,
    document.body,
  );
}

export default function Answer({ text, sources, streaming, dir, evidence }: {
  text: string; sources: Source[]; streaming: boolean; dir?: "ltr" | "rtl"; evidence?: Evidence[];
}) {
  const byN = new Map(sources.map((s) => [String(s.n), s]));
  const byKey = new Map((evidence ?? []).map((e) => [`${e.n}-${e.k}`, e]));
  const [open, setOpen] = useState<Open | null>(null);
  const closeTimer = useRef<number | undefined>(undefined);

  const cancelClose = () => window.clearTimeout(closeTimer.current);
  const closeSoon = () => {
    cancelClose();
    closeTimer.current = window.setTimeout(() => setOpen((o) => (o && !o.pinned ? null : o)), 180);
  };

  useEffect(() => {
    if (!open) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    const away = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (!t.closest(".evidence-card") && !t.closest(".cite")) setOpen(null);
    };
    const scroll = () => setOpen(null);
    window.addEventListener("keydown", esc);
    window.addEventListener("mousedown", away);
    window.addEventListener("scroll", scroll, true);
    return () => {
      window.removeEventListener("keydown", esc);
      window.removeEventListener("mousedown", away);
      window.removeEventListener("scroll", scroll, true);
    };
  }, [open]);

  useEffect(() => setOpen(null), [text]);

  const openEv = open ? byKey.get(open.key) : undefined;
  const openSrc = openEv ? byN.get(String(openEv.n)) : undefined;

  return (
    <div dir={dir ?? "auto"} className={`prose-answer ${streaming ? "caret" : ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href, children }) {
            const m = href?.match(/^#cite-(\d+)-(\d+)$/);
            if (m) {
              const s = byN.get(m[1]);
              if (!s) return <span className="cite">{m[1]}</span>;
              const key = `${m[1]}-${m[2]}`;
              if (!byKey.has(key)) {
                return (
                  <a className="cite" href={s.url} target="_blank" rel="noreferrer" title={`${s.title} — ${s.domain}`}>
                    {m[1]}
                  </a>
                );
              }
              const active = open?.key === key;
              return (
                <button
                  type="button"
                  className={`cite ${active ? "cite-active" : ""}`}
                  aria-expanded={active}
                  aria-label={`Citation ${m[1]}: show the supporting passage from ${s.title}`}
                  onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    setOpen((o) => (o?.key === key && o.pinned ? null : { key, rect, pinned: true }));
                  }}
                  onMouseEnter={(e) => {
                    if (!canHover()) return;
                    cancelClose();
                    const rect = e.currentTarget.getBoundingClientRect();
                    setOpen((o) => (o?.pinned && o.key !== key ? o : o?.key === key ? o : { key, rect, pinned: false }));
                  }}
                  onMouseLeave={closeSoon}
                >
                  {m[1]}
                </button>
              );
            }
            return (
              <a href={href} target="_blank" rel="noreferrer">
                {children}
              </a>
            );
          },
        }}
      >
        {linkCitations(text)}
      </ReactMarkdown>
      {open && openEv && openSrc && (
        <EvidenceCard
          ev={openEv} source={openSrc} rect={open.rect}
          onClose={() => setOpen(null)} onEnter={cancelClose} onLeave={closeSoon}
        />
      )}
    </div>
  );
}
