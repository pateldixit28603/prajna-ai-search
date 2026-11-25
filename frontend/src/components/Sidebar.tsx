import { Cpu, Database, MessageSquare, Plus, Trash2, X } from "lucide-react";
import type { Health, ThreadSummary } from "../lib/api";

type Props = {
  threads: ThreadSummary[];
  current: string | null;
  health: Health | null;
  open: boolean;
  onClose: () => void;
  onNew: () => void;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
};

export function Logo() {
  return (
    <span className="flex items-center gap-2">
      <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden>
        <circle cx="16" cy="16" r="14" fill="#76b900" />
        <circle cx="16" cy="16" r="6" fill="#0b0f0a" />
        <circle cx="16" cy="16" r="2.2" fill="#76b900" />
      </svg>
      <span className="font-display text-xl font-semibold tracking-tight">Prajna</span>
    </span>
  );
}

export default function Sidebar({ threads, current, health, open, onClose, onNew, onOpen, onDelete }: Props) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/50 md:hidden" onClick={onClose} />}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-line bg-panel transition-transform md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4">
          <Logo />
          <button onClick={onClose} className="text-muted md:hidden" aria-label="Close menu"><X size={18} /></button>
        </div>
        <div className="px-3">
          <button
            onClick={onNew}
            className="flex w-full items-center justify-between rounded-xl border border-line px-3 py-2.5 text-sm transition hover:border-nv/60"
          >
            <span className="flex items-center gap-2"><Plus size={15} /> New search</span>
            <kbd className="font-mono text-[10px] text-muted">/</kbd>
          </button>
        </div>

        <p className="mt-6 px-4 text-[11px] font-medium tracking-wider text-muted uppercase">History</p>
        <nav className="scroll-thin mt-2 flex-1 overflow-y-auto px-2">
          {threads.length === 0 && <p className="px-2 py-3 text-xs text-muted">Your searches will appear here.</p>}
          {threads.map((t) => (
            <div
              key={t.id}
              className={`group flex items-center rounded-lg text-sm ${current === t.id ? "bg-panel-2 text-text" : "text-text/75 hover:bg-panel-2"}`}
            >
              <button onClick={() => onOpen(t.id)} className="flex min-w-0 flex-1 items-center gap-2 px-2.5 py-2 text-left">
                <MessageSquare size={13} className="shrink-0 text-muted" />
                <span className="truncate">{t.title}</span>
              </button>
              <button
                onClick={() => onDelete(t.id)}
                className="mr-1 hidden rounded p-1 text-muted hover:text-red-400 group-hover:block"
                aria-label="Delete thread"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </nav>

        <div className="space-y-2 border-t border-line p-4 text-xs text-muted">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${health?.nvidia ? "bg-nv shadow-[0_0_8px_#76b900]" : "bg-amber-500"}`} />
            <Cpu size={13} />
            {health ? (health.nvidia ? "NVIDIA NIM connected" : "Extractive mode (no NIM key)") : "Connecting…"}
          </div>
          {health?.nvidia && <p className="truncate pl-4 font-mono text-[10px]" title={health.models.llm}>{health.models.llm}</p>}
          {health?.local_index && (
            <div className="flex items-center gap-2 pl-4">
              <Database size={12} /> {health.local_index.chunks.toLocaleString()} local chunks
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
