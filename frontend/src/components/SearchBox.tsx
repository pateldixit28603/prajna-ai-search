import { ArrowUp, BookOpen, Cpu, Database, GraduationCap, Globe, Languages, Palette, RectangleHorizontal, RectangleVertical, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { LANGS } from "../lib/langs";

export const FOCUS = [
  { id: "all", label: "All", icon: Globe, hint: "Wikipedia, OpenAlex, arXiv, Hacker News" },
  { id: "wiki", label: "Encyclopedia", icon: BookOpen, hint: "Wikipedia (+ your index)" },
  { id: "academic", label: "Academic", icon: GraduationCap, hint: "OpenAlex + arXiv papers" },
  { id: "tech", label: "Tech", icon: Cpu, hint: "Hacker News + arXiv" },
  { id: "local", label: "My index", icon: Database, hint: "Your ingested open datasets" },
  { id: "image", label: "Create image", icon: Palette, hint: "Generate an image with NVIDIA visual GenAI (FLUX)" },
];

const ASPECTS = [
  { id: "square", label: "Square", icon: Square },
  { id: "landscape", label: "Wide", icon: RectangleHorizontal },
  { id: "portrait", label: "Tall", icon: RectangleVertical },
];

type Props = {
  onSubmit: (q: string) => void;
  focus: string;
  setFocus: (f: string) => void;
  lang: string;
  setLang: (l: string) => void;
  aspect: string;
  setAspect: (a: string) => void;
  busy?: boolean;
  compact?: boolean;
  placeholder?: string;
};

export default function SearchBox({ onSubmit, focus, setFocus, lang, setLang, aspect, setAspect, busy, compact, placeholder }: Props) {
  const [q, setQ] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [q]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "TEXTAREA") {
        e.preventDefault();
        ref.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = () => {
    const v = q.trim();
    if (!v || busy) return;
    onSubmit(v);
    setQ("");
  };

  return (
    <div className={`rounded-2xl bg-panel glow transition focus-within:shadow-[0_0_0_1px_#76b900] ${compact ? "" : "p-1"}`}>
      <textarea
        ref={ref}
        rows={compact ? 1 : 2}
        value={q}
        autoFocus={!compact}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder={focus === "image" ? "Describe an image… e.g. a tiger walking through Mumbai rain at night" : placeholder ?? "Kuch bhi poochho… Ask anything"}
        className="w-full resize-none bg-transparent px-4 pt-3.5 pb-1 text-[1.02rem] outline-none placeholder:text-muted"
        aria-label="Search query"
      />
      <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
        <div className="flex flex-wrap gap-1">
          {FOCUS.filter((f) => f.id !== "image").map(({ id, label, icon: Icon, hint }) => (
            <button
              key={id}
              title={hint}
              onClick={() => setFocus(id)}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                focus === id ? "bg-nv-soft text-nv" : "text-muted hover:bg-panel-2 hover:text-text"
              }`}
            >
              <Icon size={13} />
              <span className={compact && id !== "image" ? "hidden sm:inline" : ""}>{label}</span>
            </button>
          ))}
          {focus === "image" ? (
            <div className="flex items-center gap-0.5 ps-1" role="group" aria-label="Image shape">
              {ASPECTS.map(({ id, label, icon: Icon }) => (
                <button key={id} title={label} aria-pressed={aspect === id} onClick={() => setAspect(id)}
                  className={`grid h-7 w-7 place-items-center rounded-md transition ${aspect === id ? "bg-nv-soft text-nv" : "text-muted hover:bg-panel-2 hover:text-text"}`}>
                  <Icon size={13} />
                </button>
              ))}
            </div>
          ) : (
          <label
            title="Answer language. Auto detects it from your question."
            className={`flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium transition hover:bg-panel-2 ${
              lang !== "auto" ? "bg-nv-soft text-nv" : "text-muted hover:text-text"
            }`}
          >
            <Languages size={13} />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label="Answer language"
              className="cursor-pointer bg-transparent outline-none [&>option]:bg-panel [&>option]:text-text"
            >
              <option value="auto">Auto</option>
              {LANGS.map((l) => (
                <option key={l.code} value={l.code}>{l.native}</option>
              ))}
            </select>
          </label>
          )}
        </div>
        <button
          onClick={submit}
          disabled={!q.trim() || busy}
          aria-label="Search"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-nv text-ink transition hover:brightness-110 disabled:bg-panel-2 disabled:text-muted"
        >
          <ArrowUp size={18} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
