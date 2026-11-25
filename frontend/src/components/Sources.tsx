import { ExternalLink } from "lucide-react";
import { useState } from "react";
import type { Source } from "../lib/api";

const BADGE: Record<string, string> = {
  wikipedia: "W",
  arxiv: "aX",
  openalex: "OA",
  hackernews: "Y",
  local: "◆",
};

export function SourceBadge({ s, size = 20 }: { s: Source; size?: number }) {
  return (
    <span
      className="grid shrink-0 place-items-center rounded-md bg-panel-2 font-mono text-[10px] font-semibold text-nv"
      style={{ width: size, height: size }}
    >
      {BADGE[s.source] ?? s.domain.slice(0, 1).toUpperCase()}
    </span>
  );
}

export function SourceSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="shimmer h-[84px] rounded-xl" />
      ))}
    </div>
  );
}

export default function Sources({ sources }: { sources: Source[] }) {
  const [all, setAll] = useState(false);
  const shown = all ? sources : sources.slice(0, 3);
  const rest = sources.length - 3;

  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      {shown.map((s) => (
        <a
          key={s.id}
          id={`src-${s.n}`}
          href={s.url}
          target="_blank"
          rel="noreferrer"
          className="group flex flex-col justify-between rounded-xl border border-line bg-panel p-3 transition hover:border-nv/60 hover:bg-panel-2"
          title={s.snippet}
        >
          <p className="line-clamp-2 text-[13px] leading-snug font-medium">{s.title}</p>
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-muted">
            <SourceBadge s={s} size={16} />
            <span className="truncate">{s.domain}</span>
            <span className="ml-auto font-mono text-nv">{s.n}</span>
          </div>
        </a>
      ))}
      {!all && rest > 0 && (
        <button
          onClick={() => setAll(true)}
          className="flex flex-col justify-between rounded-xl border border-dashed border-line p-3 text-left text-[13px] text-muted transition hover:border-nv/60 hover:text-text"
        >
          <div className="flex -space-x-1">
            {sources.slice(3, 7).map((s) => (
              <SourceBadge key={s.id} s={s} size={18} />
            ))}
          </div>
          <span>View {rest} more</span>
        </button>
      )}
    </div>
  );
}

export function SourceList({ sources }: { sources: Source[] }) {
  return (
    <ol className="space-y-2">
      {sources.map((s) => (
        <li key={s.id} className="flex gap-3 rounded-xl border border-line bg-panel p-3">
          <span className="font-mono text-xs text-nv">{s.n}</span>
          <div className="min-w-0 flex-1">
            <a href={s.url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-sm font-medium hover:text-nv">
              {s.title} <ExternalLink size={12} className="opacity-50" />
            </a>
            <p className="mt-0.5 text-xs text-muted">
              {s.domain}
              {s.published ? ` · ${s.published}` : ""}
              {s.authors?.length ? ` · ${s.authors.slice(0, 3).join(", ")}` : ""}
              {typeof s.extra?.cited_by === "number" ? ` · ${s.extra.cited_by} citations` : ""}
              {typeof s.extra?.points === "number" ? ` · ${s.extra.points} points` : ""}
            </p>
            <p className="mt-1.5 line-clamp-3 text-[13px] leading-relaxed text-text/80">{s.snippet}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
