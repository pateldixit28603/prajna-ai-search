import { AlertTriangle, Check, Copy, Download, Palette, RefreshCw, Wand2, Zap } from "lucide-react";
import { useState } from "react";
import type { Turn } from "../lib/api";

const RATIO: Record<string, string> = { square: "1 / 1", landscape: "16 / 9", portrait: "9 / 16" };

export default function ImageTurn({ turn, onVariation, busy }: {
  turn: Turn; onVariation: (prompt: string, aspect: string) => void; busy: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const img = turn.image;
  const aspect = img?.aspect ?? turn.status ?? "square";
  const name = (turn.question.replace(/[^\p{L}\p{N}]+/gu, "-").slice(0, 40) || "prajna") + ".png";

  return (
    <article className="border-b border-line pb-10">
      <h2 dir="auto" className="flex items-start gap-2 font-display text-[1.7rem] leading-tight font-semibold tracking-tight md:text-3xl">
        <Palette size={22} className="mt-1.5 shrink-0 text-nv" /> {turn.question}
      </h2>

      <div className={`mt-5 ${aspect === "portrait" ? "max-w-sm" : aspect === "landscape" ? "max-w-3xl" : "max-w-xl"}`}>
        {img ? (
          <a href={img.image} download={name} title="Download">
            <img src={img.image} alt={img.prompt} className="w-full rounded-2xl border border-line" style={{ aspectRatio: RATIO[img.aspect] }} />
          </a>
        ) : turn.stage === "error" ? null : (
          <div className="shimmer grid w-full place-items-center rounded-2xl text-xs text-muted" style={{ aspectRatio: RATIO[aspect] ?? "1 / 1" }}>
            <span className="flex items-center gap-2"><Wand2 size={14} className="animate-pulse text-nv" /> Painting with NVIDIA visual GenAI…</span>
          </div>
        )}
      </div>

      {turn.error && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-300">
          <AlertTriangle size={16} /> {turn.error}
        </div>
      )}

      {img && (
        <>
          {img.enhanced && (
            <p className="mt-4 max-w-3xl text-[13px] leading-relaxed text-text/75">
              <span className="me-1.5 rounded bg-nv-soft px-1.5 py-0.5 font-mono text-[10px] text-nv">Nemotron prompt</span>
              {img.prompt}
            </p>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
            <a href={img.image} download={name} className="flex items-center gap-1.5 rounded-lg px-2 py-1 hover:bg-panel hover:text-text">
              <Download size={13} /> Download
            </a>
            <button disabled={busy} onClick={() => onVariation(turn.question, img.aspect)}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 hover:bg-panel hover:text-text disabled:opacity-50">
              <RefreshCw size={13} /> Variation
            </button>
            <button onClick={async () => { await navigator.clipboard.writeText(img.prompt); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 hover:bg-panel hover:text-text">
              {copied ? <Check size={13} className="text-nv" /> : <Copy size={13} />} {copied ? "Copied" : "Copy prompt"}
            </button>
            <span className="flex items-center gap-1" title={`seed ${img.seed}`}>
              <Zap size={12} className="text-nv" /> {img.total.toFixed(1)}s · {img.model.split("/")[1] ?? img.model} on NVIDIA NIM
            </span>
          </div>
        </>
      )}
    </article>
  );
}
