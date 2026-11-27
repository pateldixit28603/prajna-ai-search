import {
  AlertTriangle, Check, Copy, Download, ImagePlus, Loader2, Maximize2, RectangleHorizontal, RectangleVertical,
  RefreshCw, Sparkles, Square, Wand2, X, Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ImageResult } from "../lib/api";

export type StudioItem = {
  id: string;
  idea: string;
  style: string;
  aspect: string;
  status: "pending" | "done" | "error";
  image?: ImageResult;
  error?: string;
};

export const STYLES = [
  { id: "none", label: "Auto" },
  { id: "photo", label: "Photo" },
  { id: "cinematic", label: "Cinematic" },
  { id: "anime", label: "Anime" },
  { id: "3d", label: "3D render" },
  { id: "digital-art", label: "Digital art" },
  { id: "watercolor", label: "Watercolor" },
  { id: "pixel", label: "Pixel art" },
  { id: "minimal", label: "Minimal / logo" },
];

const ASPECTS = [
  { id: "square", label: "Square", hint: "1:1", icon: Square },
  { id: "landscape", label: "Wide", hint: "16:9", icon: RectangleHorizontal },
  { id: "portrait", label: "Tall", hint: "9:16", icon: RectangleVertical },
];

const RATIO: Record<string, string> = { square: "1 / 1", landscape: "16 / 9", portrait: "9 / 16" };

const IDEAS = [
  { text: "A tiger walking through Mumbai rain at night, neon reflections", style: "cinematic" },
  { text: "Diwali night on the Varanasi ghats, thousands of oil lamps", style: "photo" },
  { text: "A cozy reading nook inside a giant teacup", style: "3d" },
  { text: "An astronaut drinking chai on Mars at sunset", style: "digital-art" },
  { text: "A minimal logo of a green owl made of circuit lines", style: "minimal" },
  { text: "Studio Ghibli-like village in the Himalayas, spring morning", style: "anime" },
];

const fileName = (s: string) => (s.replace(/[^\p{L}\p{N}]+/gu, "-").slice(0, 40) || "prajna") + ".png";

function ImageCard({ item, onOpen, onVariation, onReuse, busy }: {
  item: StudioItem; onOpen: () => void; onVariation: () => void; onReuse: () => void; busy: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const img = item.image;
  const styleLabel = STYLES.find((s) => s.id === item.style)?.label;
  return (
    <figure className="studio-card mb-4 break-inside-avoid overflow-hidden rounded-2xl border border-line bg-panel">
      {item.status === "pending" ? (
        <div className="shimmer grid place-items-center" style={{ aspectRatio: RATIO[item.aspect] ?? "1 / 1" }}>
          <span className="flex flex-col items-center gap-2 text-xs text-muted">
            <Wand2 size={18} className="animate-pulse text-nv" />
            Painting with NVIDIA visual GenAI…
          </span>
        </div>
      ) : item.status === "error" ? (
        <div className="grid place-items-center bg-red-950/20 p-6 text-center" style={{ aspectRatio: RATIO[item.aspect] ?? "1 / 1" }}>
          <span className="flex max-w-xs flex-col items-center gap-2 text-sm text-red-300">
            <AlertTriangle size={18} /> {item.error}
          </span>
        </div>
      ) : img ? (
        <div className="group relative">
          <button onClick={onOpen} className="block w-full" aria-label="Open full size">
            <img src={img.image} alt={img.prompt} className="w-full" style={{ aspectRatio: RATIO[img.aspect] }} />
          </button>
          <div className="pointer-events-none absolute inset-x-0 top-0 flex justify-end gap-1.5 p-2 opacity-100 transition md:opacity-0 md:group-hover:opacity-100">
            <a href={img.image} download={fileName(item.idea)} title="Download"
              className="pointer-events-auto grid h-8 w-8 place-items-center rounded-lg bg-black/60 text-white backdrop-blur hover:bg-nv hover:text-ink">
              <Download size={15} />
            </a>
            <button onClick={onOpen} title="View full size"
              className="pointer-events-auto grid h-8 w-8 place-items-center rounded-lg bg-black/60 text-white backdrop-blur hover:bg-nv hover:text-ink">
              <Maximize2 size={15} />
            </button>
          </div>
        </div>
      ) : null}
      <figcaption className="space-y-2 p-3.5">
        <p dir="auto" className="line-clamp-2 text-sm text-text/90">{item.idea}</p>
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
          {styleLabel && item.style !== "none" && <span className="rounded-full border border-line px-2 py-0.5">{styleLabel}</span>}
          <span className="rounded-full border border-line px-2 py-0.5">{ASPECTS.find((a) => a.id === item.aspect)?.hint}</span>
          {img && (
            <span className="flex items-center gap-1" title={`seed ${img.seed}`}>
              <Zap size={11} className="text-nv" /> {img.total.toFixed(1)}s · {img.model.split("/")[1] ?? img.model}
            </span>
          )}
        </div>
        {item.status !== "pending" && (
          <div className="flex flex-wrap gap-1 pt-0.5 text-xs text-muted">
            {img && (
              <button disabled={busy} onClick={onVariation}
                className="flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-panel-2 hover:text-text disabled:opacity-50">
                <RefreshCw size={12} /> Variation
              </button>
            )}
            <button onClick={onReuse} className="flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-panel-2 hover:text-text">
              <ImagePlus size={12} /> Edit prompt
            </button>
            {img && (
              <button onClick={async () => { await navigator.clipboard.writeText(img.prompt); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
                className="flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-panel-2 hover:text-text">
                {copied ? <Check size={12} className="text-nv" /> : <Copy size={12} />} {copied ? "Copied" : "Copy prompt"}
              </button>
            )}
          </div>
        )}
      </figcaption>
    </figure>
  );
}

function Lightbox({ item, onClose }: { item: StudioItem; onClose: () => void }) {
  const img = item.image!;
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/90 backdrop-blur-sm" onClick={onClose} role="dialog" aria-label="Image preview">
      <div className="flex items-center justify-end gap-2 p-3">
        <a href={img.image} download={fileName(item.idea)} onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1.5 rounded-lg bg-nv px-3 py-1.5 text-sm font-medium text-ink hover:brightness-110">
          <Download size={15} /> Download
        </a>
        <button onClick={onClose} aria-label="Close" className="grid h-9 w-9 place-items-center rounded-lg text-white hover:bg-white/10"><X size={18} /></button>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center px-4">
        <img src={img.image} alt={img.prompt} onClick={(e) => e.stopPropagation()} className="max-h-full max-w-full rounded-xl object-contain" />
      </div>
      {img.enhanced && (
        <p className="mx-auto max-w-3xl p-4 text-center text-[13px] leading-relaxed text-white/70" onClick={(e) => e.stopPropagation()}>
          <span className="me-1.5 rounded bg-nv/20 px-1.5 py-0.5 font-mono text-[10px] text-nv">Nemotron prompt</span>{img.prompt}
        </p>
      )}
    </div>
  );
}

export default function Studio({ items, busy, nvidia, onGenerate }: {
  items: StudioItem[]; busy: boolean; nvidia: boolean | null;
  onGenerate: (idea: string, style: string, aspect: string, enhance: boolean) => void;
}) {
  const [idea, setIdea] = useState("");
  const [style, setStyle] = useState("none");
  const [aspect, setAspect] = useState("square");
  const [enhance, setEnhance] = useState(true);
  const [open, setOpen] = useState<StudioItem | null>(null);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(Math.max(el.scrollHeight, 84), 220) + "px";
  }, [idea]);

  const go = (text = idea, st = style, ar = aspect) => {
    const v = text.trim();
    if (v.length < 2 || busy) return;
    onGenerate(v, st, ar, enhance);
  };

  const reuse = (it: StudioItem) => {
    setIdea(it.idea);
    setStyle(it.style);
    setAspect(it.aspect);
    window.scrollTo({ top: 0, behavior: "smooth" });
    ref.current?.focus();
  };

  return (
    <div className="scroll-thin flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-4 pt-10 pb-24 md:px-8 md:pt-14">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-nv/40 bg-nv-soft px-3 py-1 text-xs font-medium text-nv">
            <Sparkles size={12} /> Prajna Studio · NVIDIA FLUX + Nemotron
          </span>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-tight md:text-5xl">
            Describe it. <span className="text-nv">See it.</span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm text-muted md:text-base">
            Describe anything, in any language. Nemotron turns your idea into a detailed prompt and NVIDIA FLUX paints it in seconds.
          </p>
        </div>

        <div className="studio-composer mx-auto mt-8 max-w-3xl rounded-2xl border border-line bg-panel p-2 glow focus-within:border-nv/70">
          <textarea
            ref={ref}
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); go(); }
            }}
            placeholder="e.g. A tiger walking through Mumbai rain at night, neon reflections…"
            aria-label="Describe the image you want"
            className="w-full resize-none bg-transparent px-3.5 pt-3 pb-2 text-[1.05rem] outline-none placeholder:text-muted"
          />
          <div className="border-t border-line px-2 pt-2.5">
            <div className="scroll-thin -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-2" role="group" aria-label="Style">
              {STYLES.map((s) => (
                <button key={s.id} onClick={() => setStyle(s.id)} aria-pressed={style === s.id}
                  className={`shrink-0 rounded-full border px-3 py-1 text-xs transition ${
                    style === s.id ? "border-nv/70 bg-nv-soft text-nv" : "border-line text-muted hover:border-nv/40 hover:text-text"
                  }`}>
                  {s.label}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 pb-1.5">
              <div className="flex items-center gap-3">
                <div className="flex rounded-lg border border-line p-0.5" role="group" aria-label="Image shape">
                  {ASPECTS.map(({ id, label, hint, icon: Icon }) => (
                    <button key={id} onClick={() => setAspect(id)} aria-pressed={aspect === id} title={`${label} ${hint}`}
                      className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs transition ${
                        aspect === id ? "bg-nv-soft text-nv" : "text-muted hover:text-text"
                      }`}>
                      <Icon size={12} /> <span className="hidden sm:inline">{label}</span>
                    </button>
                  ))}
                </div>
                <label className="flex cursor-pointer items-center gap-1.5 text-xs text-muted select-none" title="Let Nemotron Bolt expand your idea into a detailed prompt">
                  <input type="checkbox" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} className="accent-[#76b900]" />
                  Enhance prompt
                </label>
              </div>
              <button onClick={() => go()} disabled={busy || idea.trim().length < 2}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-nv px-4 py-2 text-sm font-semibold sm:w-auto text-ink transition hover:brightness-110 disabled:bg-panel-2 disabled:text-muted">
                {busy ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}
                {busy ? "Generating…" : "Generate"}
              </button>
            </div>
          </div>
        </div>

        {nvidia === false && (
          <p className="mx-auto mt-3 max-w-3xl text-center text-xs text-amber-300/90">
            Image generation needs the NVIDIA API key on the server. It isn't connected right now.
          </p>
        )}

        <div className="scroll-thin -mx-4 mt-5 flex max-w-3xl gap-2 overflow-x-auto px-4 pb-1 sm:mx-auto sm:flex-wrap sm:justify-center sm:overflow-visible">
          {IDEAS.map((x) => (
            <button key={x.text} dir="auto" disabled={busy}
              onClick={() => { setIdea(x.text); setStyle(x.style); go(x.text, x.style, aspect); }}
              className="shrink-0 rounded-full border border-line px-3 py-1.5 text-xs whitespace-nowrap text-text/75 transition hover:border-nv/60 hover:text-text disabled:opacity-50">
              {x.text}
            </button>
          ))}
        </div>

        {items.length > 0 ? (
          <section className="mt-12">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-medium text-muted">
              <ImagePlus size={15} className="text-nv" /> Your creations <span className="font-mono text-xs">{items.filter((i) => i.status === "done").length}</span>
            </h2>
            <div className="columns-1 gap-4 sm:columns-2 lg:columns-3">
              {items.map((it) => (
                <ImageCard key={it.id} item={it} busy={busy}
                  onOpen={() => setOpen(it)}
                  onVariation={() => go(it.idea, it.style, it.aspect)}
                  onReuse={() => reuse(it)} />
              ))}
            </div>
          </section>
        ) : (
          <div className="mx-auto mt-14 grid max-w-3xl gap-3 text-sm sm:grid-cols-3">
            {[
              ["1 · Describe", "Write your idea in plain words, in any language."],
              ["2 · Nemotron writes", "Bolt expands it into a detailed image prompt."],
              ["3 · FLUX paints", "NVIDIA visual GenAI returns the image in seconds."],
            ].map(([t, d]) => (
              <div key={t} className="rounded-xl border border-line p-4">
                <p className="font-medium">{t}</p>
                <p className="mt-1 text-xs text-muted">{d}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      {open?.image && <Lightbox item={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
