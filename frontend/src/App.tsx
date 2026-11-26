import { Menu } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import SearchBox from "./components/SearchBox";
import Sidebar, { Logo } from "./components/Sidebar";
import TurnView from "./components/TurnView";
import { deleteThread, getHealth, getThread, listThreads, streamSearch, type Health, type ThreadSummary, type Turn } from "./lib/api";

const EXAMPLES = [
  "NVIDIA ka CUDA kya hai aur AI ke liye kyun zaroori hai?",
  "How do retrieval-augmented generation systems reduce hallucinations?",
  "Bhagavad Gita ke 18 adhyay kaun se hain?",
  "Как работают графические процессоры NVIDIA?",
];

const emptyTurn = (question: string): Turn => ({
  question, answer: "", sources: [], followups: [], queries: [], status: "Starting…", stage: "planning", warnings: [],
});

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [focus, setFocus] = useState("all");
  const [lang, setLang] = useState("auto");
  const [busy, setBusy] = useState(false);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [menu, setMenu] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshThreads = useCallback(() => listThreads().then(setThreads).catch(() => {}), []);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
    refreshThreads();
  }, [refreshThreads]);

  const patchLast = (fn: (t: Turn) => Turn) =>
    setTurns((ts) => (ts.length ? [...ts.slice(0, -1), fn(ts[ts.length - 1])] : ts));

  const ask = async (question: string) => {
    if (busy) return;
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
  };

  const openThread = async (id: string) => {
    abortRef.current?.abort();
    const t = await getThread(id);
    setThreadId(id);
    setFocus(t.focus);
    setLang(t.lang ?? "auto");
    setTurns(t.turns.map((x: any) => ({
      question: x.question, answer: x.answer, sources: x.sources, followups: x.followups,
      queries: x.meta?.queries ?? [], status: "", stage: "done", warnings: [], meta: x.meta,
      lang: x.meta?.lang, turnId: x.id, translations: x.meta?.translations ?? {},
      shownLang: x.meta?.shown_lang ?? x.meta?.lang,
    })));
    setMenu(false);
  };

  const removeThread = async (id: string) => {
    await deleteThread(id);
    if (id === threadId) newThread();
    refreshThreads();
  };

  return (
    <div className="flex h-full">
      <Sidebar threads={threads} current={threadId} health={health} open={menu}
        onClose={() => setMenu(false)} onNew={newThread} onOpen={openThread} onDelete={removeThread} />

      <main className="relative flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line px-4 py-3 md:hidden">
          <button onClick={() => setMenu(true)} aria-label="Open menu"><Menu size={20} /></button>
          <Logo />
        </header>

        {turns.length === 0 ? (
          <section className="flex flex-1 flex-col items-center justify-center px-4 pb-24">
            <h1 className="font-display text-4xl font-semibold tracking-tight md:text-5xl">
              Where knowledge <span className="text-nv">begins.</span>
            </h1>
            <p className="mt-3 max-w-lg text-center text-sm text-muted">
              Open-source answer engine — open data from Wikipedia, OpenAlex, arXiv & Hacker News, ranked and written by NVIDIA NIM.
            </p>
            <div className="mt-8 w-full max-w-2xl">
              <SearchBox onSubmit={ask} focus={focus} setFocus={setFocus} lang={lang} setLang={setLang} busy={busy} />
            </div>
            <div className="mt-6 grid w-full max-w-2xl gap-2 sm:grid-cols-2">
              {EXAMPLES.map((ex) => (
                <button key={ex} onClick={() => ask(ex)}
                  className="rounded-xl border border-line px-3.5 py-2.5 text-left text-[13px] text-text/80 transition hover:border-nv/60 hover:text-text">
                  {ex}
                </button>
              ))}
            </div>
          </section>
        ) : (
          <>
            <div className="scroll-thin flex-1 overflow-y-auto">
              <div className="mx-auto max-w-3xl space-y-10 px-4 pt-8 pb-40 md:px-6">
                {turns.map((t, i) => (
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
                <SearchBox compact onSubmit={ask} focus={focus} setFocus={setFocus} lang={lang} setLang={setLang} busy={busy} placeholder="Ask a follow-up…" />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
