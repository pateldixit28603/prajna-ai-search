import { ArrowUp, BookOpen, Cpu, Database, GraduationCap, Globe } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export const FOCUS = [
  { id: "all", label: "All", icon: Globe, hint: "Wikipedia, OpenAlex, arXiv, Hacker News" },
  { id: "wiki", label: "Encyclopedia", icon: BookOpen, hint: "Wikipedia (+ your index)" },
  { id: "academic", label: "Academic", icon: GraduationCap, hint: "OpenAlex + arXiv papers" },
  { id: "tech", label: "Tech", icon: Cpu, hint: "Hacker News + arXiv" },
  { id: "local", label: "My index", icon: Database, hint: "Your ingested open datasets" },
];

type Props = {
  onSubmit: (q: string) => void;
  focus: string;
  setFocus: (f: string) => void;
  busy?: boolean;
  compact?: boolean;
  placeholder?: string;
};

export default function SearchBox({ onSubmit, focus, setFocus, busy, compact, placeholder }: Props) {
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
        placeholder={placeholder ?? "Kuch bhi poochho… Ask anything"}
        className="w-full resize-none bg-transparent px-4 pt-3.5 pb-1 text-[1.02rem] outline-none placeholder:text-muted"
        aria-label="Search query"
      />
      <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
        <div className="flex flex-wrap gap-1">
          {FOCUS.map(({ id, label, icon: Icon, hint }) => (
            <button
              key={id}
              title={hint}
              onClick={() => setFocus(id)}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                focus === id ? "bg-nv-soft text-nv" : "text-muted hover:bg-panel-2 hover:text-text"
              }`}
            >
              <Icon size={13} />
              <span className={compact ? "hidden sm:inline" : ""}>{label}</span>
            </button>
          ))}
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
