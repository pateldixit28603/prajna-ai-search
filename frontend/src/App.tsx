import { ArrowRight, BookOpen, Cpu, Globe2, GraduationCap, Menu, Search, Sparkles, Wand2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ImageTurn from "./components/ImageTurn";
import SearchBox from "./components/SearchBox";
import Sidebar, { Logo } from "./components/Sidebar";
import Studio, { type StudioItem } from "./components/Studio";
import TurnView from "./components/TurnView";
import { createImage, deleteThread, getHealth, getThread, listThreads, streamSearch, type Health, type ThreadSummary, type Turn } from "./lib/api";

const EXAMPLES = [
  { q: "What is NVIDIA CUDA and why does it matter for AI?", tag: "Tech", icon: Cpu },
  { q: "How do retrieval-augmented generation systems reduce hallucinations?", tag: "Research", icon: GraduationCap },
  { q: "What are the 18 chapters of the Bhagavad Gita?", tag: "Encyclopedia", icon: BookOpen },
  { q: "How did India land Chandrayaan-3 near the Moon's south pole?", tag: "Science", icon: Globe2 },
];

type View = "search" | "studio";
const viewFromHash = (): View => (window.location.hash === "#create" ? "studio" : "search");

const emptyTurn = (question: string): Turn => ({
  question, answer: "", sources: [], followups: [], queries: [], status: "Starting…", stage: "planning", warnings: [],
});

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [focus, setFocus] = useState("all");
  const [lang, setLang] = useState("auto");
  const [aspect, setAspect] = useState("square");
  const [busy, setBusy] = useState(false);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [menu, setMenu] = useState(false);
  const [view, setViewState] = useState<View>(viewFromHash);
  const [studioItems, setStudioItems] = useState<StudioItem[]>([]);
  const [studioThread, setStudioThread] = useState<string | null>(null);
  const [studioBusy, setStudioBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const setView = (v: View) => {
    setViewState(v);
    setMenu(false);
    const hash = v === "studio" ? "#create" : "";
    if (window.location.hash !== hash) history.replaceState(null, "", hash || window.location.pathname);
  };

  useEffect(() => {
    const on = () => setViewState(viewFromHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  const generate = async (idea: string, style: string, shape: string, enhance: boolean) => {
    if (studioBusy) return;
    const id = `${Date.now()}`;
    setStudioBusy(true);
    setStudioItems((xs) => [{ id, idea, style, aspect: shape, status: "pending" }, ...xs]);
    const patch = (fn: (x: StudioItem) => StudioItem) => setStudioItems((xs) => xs.map((x) => (x.id === id ? fn(x) : x)));
    try {
      const img = await createImage({ prompt: idea, aspect: shape, enhance, style, thread_id: studioThread });
      patch((x) => ({ ...x, status: "done", image: img }));
      if (img.thread_id) setStudioThread(img.thread_id);
      refreshThreads();
    } catch (err) {
      patch((x) => ({ ...x, status: "error", error: (err as Error).message || "Image generation failed." }));
    } finally {
      setStudioBusy(false);
    }
  };

  const refreshThreads = useCallback(() => listThreads().then(setThreads).catch(() => {}), []);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
    refreshThreads();
  }, [refreshThreads]);

  const patchLast = (fn: (t: Turn) => Turn) =>
    setTurns((ts) => (ts.length ? [...ts.slice(0, -1), fn(ts[ts.length - 1])] : ts));

  const imagine = async (prompt: string, shape = aspect) => {
    if (busy) return;
    setBusy(true);
    setMenu(false);
    setTurns((ts) => [...ts, { ...emptyTurn(prompt), kind: "image", status: shape }]);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    try {
      const img = await createImage({ prompt, aspect: shape, enhance: true, thread_id: threadId });
      patchLast((t) => ({ ...t, stage: "done", image: img, turnId: img.turn_id }));
      if (img.thread_id) setThreadId(img.thread_id);
      refreshThreads();
    } catch (err) {
      patchLast((t) => ({ ...t, stage: "error", error: (err as Error).message || "Image generation failed." }));
    } finally {
      setBusy(false);
    }
  };

  const ask = async (question: string) => {
    if (busy) return;
    setView("search");
    setBusy(true);
    setMenu(false);
    setTurns((ts) => [...ts, emptyTurn(question)]);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      await streamSearch({ query: question, focus, thread_id: threadId, lang: lang === "auto" ? null : lang }, (e) => {
        switch (e.type) {
          case "status":
            patchLast((t) => ({ ...t, status: e.message, stage: e.stage }));
            break;
          case "lang":
            patchLast((t) => ({ ...t, lang: e.lang, shownLang: e.lang }));
            break;
          case "queries":
            patchLast((t) => ({ ...t, queries: e.queries }));
            break;
          case "sources":
            patchLast((t) => ({ ...t, sources: e.sources, warnings: e.warnings ?? [] }));
            break;
          case "token":
            patchLast((t) => ({ ...t, answer: t.answer + e.text, stage: "writing" }));
            break;
          case "replace":
            patchLast((t) => ({ ...t, answer: e.text }));
            break;
          case "evidence":
            patchLast((t) => ({ ...t, evidence: e.items ?? [] }));
            break;
          case "followups":
            patchLast((t) => ({ ...t, followups: e.questions }));
            break;
          case "done":
            patchLast((t) => ({ ...t, stage: "done", meta: e.meta, turnId: e.turn_id }));
            setThreadId(e.thread_id);
            refreshThreads();
            break;
          case "error":
            patchLast((t) => ({ ...t, stage: "error", error: e.message }));
            break;
        }
      }, ctrl.signal);
    } catch (err) {
      if ((err as Error).name !== "AbortError")
        patchLast((t) => ({ ...t, stage: "error", error: "Could not reach the Prajna backend. Is it running on :8000?" }));
    } finally {
      setBusy(false);
    }
  };

  const newThread = () => {
    abortRef.current?.abort();
    setTurns([]);
    setThreadId(null);
    setLang("auto");
    setMenu(false);
    setView("search");
  };

  const openThread = async (id: string) => {
    abortRef.current?.abort();
    const t = await getThread(id);
    if (t.focus === "image") {   // image threads open in the Studio gallery
      setStudioThread(id);
      setStudioItems(t.turns.filter((x: any) => x.meta?.kind === "image").reverse().map((x: any): StudioItem => ({
        id: `t${x.id}`, idea: x.question, style: x.meta.style ?? "none", aspect: x.meta.aspect, status: "done",
        image: { image: x.meta.image, model: x.meta.model, seed: x.meta.seed, aspect: x.meta.aspect,
                 prompt: x.meta.prompt, enhanced: x.meta.enhanced, total: x.meta.total, style: x.meta.style },
      })));
      setView("studio");
      return;
    }
    setView("search");
    setThreadId(id);
    setFocus(t.focus);
    setLang(t.lang ?? "auto");
    setTurns(t.turns.map((x: any): Turn => x.meta?.kind === "image" ? ({
      ...emptyTurn(x.question), kind: "image", stage: "done", turnId: x.id,
      image: { image: x.meta.image, model: x.meta.model, seed: x.meta.seed, aspect: x.meta.aspect,
               prompt: x.meta.prompt, enhanced: x.meta.enhanced, total: x.meta.total },
    }) : ({
      question: x.question, answer: x.answer, sources: x.sources, followups: x.followups,
      queries: x.meta?.queries ?? [], status: "", stage: "done", warnings: [], meta: x.meta,
      lang: x.meta?.lang, turnId: x.id, translations: x.meta?.translations ?? {},
      shownLang: x.meta?.shown_lang ?? x.meta?.lang, evidence: x.meta?.evidence ?? [],
    })));
    setMenu(false);
  };

  const removeThread = async (id: string) => {
    await deleteThread(id);
    if (id === threadId) newThread();
    if (id === studioThread) { setStudioThread(null); setStudioItems([]); }
    refreshThreads();
  };

  return (
    <div className="flex h-full">
      <Sidebar threads={threads} current={threadId} health={health} open={menu}
        onClose={() => setMenu(false)} onNew={newThread} onStudio={() => setView("studio")} onOpen={openThread} onDelete={removeThread} />

      <main className="relative flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line bg-ink/80 px-3 py-2.5 backdrop-blur md:px-6">
          <button className="md:hidden" onClick={() => setMenu(true)} aria-label="Open menu"><Menu size={20} /></button>
          <span className="md:hidden"><Logo /></span>
          <nav className="mx-auto flex rounded-xl border border-line bg-panel p-1 md:mx-0" aria-label="Mode">
            {([["search", "Search", Search], ["studio", "Create image", Wand2]] as const).map(([v, label, Icon]) => (
              <button key={v} onClick={() => setView(v)} aria-current={view === v ? "page" : undefined}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  view === v ? "bg-nv text-ink" : "text-muted hover:text-text"
                }`}>
                <Icon size={14} /> {label}
              </button>
            ))}
          </nav>
          <span className="ms-auto hidden items-center gap-2 text-xs text-muted md:flex">
            <span className={`h-2 w-2 rounded-full ${health?.nvidia ? "bg-nv shadow-[0_0_8px_#76b900]" : "bg-amber-500"}`} />
            {health ? (health.nvidia ? "NVIDIA NIM online" : "Extractive mode") : "Connecting…"}
          </span>
        </header>

        {view === "studio" ? (
          <Studio items={studioItems} busy={studioBusy} nvidia={health ? health.nvidia : null} onGenerate={generate} />
        ) : turns.length === 0 ? (
          <section className="scroll-thin flex flex-1 flex-col items-center overflow-y-auto px-4 pt-[12vh] pb-16">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1 text-xs text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-nv" /> Open-source answer engine on NVIDIA NIM
            </span>
            <h1 className="mt-5 text-center font-display text-4xl font-semibold tracking-tight md:text-6xl">
              Where knowledge <span className="text-nv">begins.</span>
            </h1>
            <p className="mt-4 max-w-xl text-center text-sm text-muted md:text-base">
              Cited answers from Wikipedia, OpenAlex, arXiv and Hacker News, searched, reranked and written by NVIDIA Nemotron, in 7 languages.
            </p>
            <div className="mt-9 w-full max-w-2xl">
              <SearchBox onSubmit={ask} focus={focus} setFocus={setFocus} lang={lang} setLang={setLang} aspect={aspect} setAspect={setAspect} busy={busy} />
            </div>
            <div className="mt-5 grid w-full max-w-2xl gap-2 sm:grid-cols-2">
              {EXAMPLES.map(({ q, tag, icon: Icon }) => (
                <button key={q} onClick={() => ask(q)} dir="auto"
                  className="group flex items-start gap-3 rounded-xl border border-line bg-panel/40 px-3.5 py-3 text-left transition hover:border-nv/60 hover:bg-panel">
                  <Icon size={16} className="mt-0.5 shrink-0 text-muted group-hover:text-nv" />
                  <span className="min-w-0">
                    <span className="block text-[13px] text-text/85 group-hover:text-text">{q}</span>
                    <span className="mt-1 block text-[11px] text-muted">{tag}</span>
                  </span>
                </button>
              ))}
            </div>
            <button onClick={() => setView("studio")}
              className="group mt-4 flex w-full max-w-2xl items-center gap-4 rounded-2xl border border-nv/40 bg-gradient-to-r from-nv/15 via-panel to-panel p-4 text-left transition hover:border-nv">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-nv text-ink"><Sparkles size={20} /></span>
              <span className="min-w-0 flex-1">
                <span className="block font-medium">Create images with AI</span>
                <span className="block text-xs text-muted">Type a prompt and get an image in seconds · NVIDIA FLUX + Nemotron, 9 styles</span>
              </span>
              <ArrowRight size={18} className="shrink-0 text-nv transition group-hover:translate-x-0.5" />
            </button>
            <div className="mt-10 flex flex-wrap justify-center gap-x-5 gap-y-2 text-[11px] text-muted">
              <span><b className="font-medium text-text/80">Nemotron Bolt</b> plans queries</span>
              <span><b className="font-medium text-text/80">Embed 1B + Rerank 8B</b> rank passages</span>
              <span><b className="font-medium text-text/80">Nemotron Lightning</b> writes cited answers</span>
              <span><b className="font-medium text-text/80">FLUX.2</b> creates images</span>
            </div>
          </section>
        ) : (
          <>
            <div className="scroll-thin flex-1 overflow-y-auto">
              <div className="mx-auto max-w-3xl space-y-10 px-4 pt-8 pb-40 md:px-6">
                {turns.map((t, i) => t.kind === "image" ? (
                  <ImageTurn key={i} turn={t} busy={busy} onVariation={(p, a) => imagine(p, a)} />
                ) : (
                  <TurnView key={i} turn={t} live={i === turns.length - 1 && busy} onFollowup={ask}
                    threadId={threadId} onLang={(code, text) => {
                      setLang(code);
                      setTurns((ts) => ts.map((x, j) => j === i
                        ? { ...x, shownLang: code, translations: text ? { ...(x.translations ?? {}), [code]: text } : x.translations }
                        : x));
                    }} />
                ))}
                <div ref={bottomRef} />
              </div>
            </div>
            <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink via-ink/95 to-transparent pt-10 pb-5">
              <div className="pointer-events-auto mx-auto max-w-3xl px-4 md:px-6">
                <SearchBox compact onSubmit={ask} focus={focus} setFocus={setFocus} lang={lang} setLang={setLang} aspect={aspect} setAspect={setAspect} busy={busy} placeholder="Ask a follow-up…" />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
