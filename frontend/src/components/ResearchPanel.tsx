import { BookOpen, ExternalLink, FileText, Flame, Landmark, Loader2, Quote, Sparkles, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { getResearch, type Paper, type Research } from "../lib/api";

const fmt = (n: number) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(n >= 1e4 ? 0 : 1)}k` : `${n}`);

function PaperCard({ p }: { p: Paper }) {
  return (
    <li className="rounded-xl border border-line p-3.5 transition hover:border-nv/50">
      <div className="flex items-start gap-3">
        <a href={p.url} target="_blank" rel="noreferrer" className="flex-1 text-[15px] leading-snug font-medium hover:text-nv">
          {p.title}
        </a>
        <span title="Times cited (OpenAlex)" className="flex shrink-0 items-center gap-1 rounded-full bg-nv-soft px-2 py-0.5 font-mono text-[11px] text-nv">
          <Quote size={10} /> {fmt(p.cited_by)}
        </span>
      </div>
      <p className="mt-1 text-xs text-muted">
        {[p.authors.join(", "), p.venue, p.year].filter(Boolean).join(" · ")}
      </p>
      {p.abstract && <p className="mt-2 text-[13px] leading-relaxed text-text/75">{p.abstract}</p>}
      <div className="mt-2 flex gap-3 text-xs">
        {p.oa_url && (
          <a href={p.oa_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-nv hover:underline">
            <FileText size={12} /> Free full text
          </a>
        )}
        <a href={p.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-muted hover:text-text">
          <ExternalLink size={12} /> Publisher / DOI
        </a>
      </div>
    </li>
  );
}

function Section({ icon: Icon, title, hint, papers }: { icon: typeof Flame; title: string; hint: string; papers: Paper[] }) {
  if (!papers.length) return null;
  return (
    <section className="mt-7">
      <h3 className="flex items-center gap-2 text-sm font-medium"><Icon size={15} className="text-nv" /> {title}</h3>
      <p className="mb-2.5 text-xs text-muted">{hint}</p>
      <ul className="space-y-2">{papers.map((p) => <PaperCard key={p.id} p={p} />)}</ul>
    </section>
  );
}

function Timeline({ rows, peak }: { rows: Research["timeline"]; peak: number | null }) {
  if (rows.length < 2) return null;
  const max = Math.max(...rows.map((r) => r.count), 1);
  return (
    <section className="mt-6">
      <h3 className="flex items-center gap-2 text-sm font-medium"><TrendingUp size={15} className="text-nv" /> Research timeline</h3>
      <p className="mb-3 text-xs text-muted">Works published per year{peak ? ` · peak in ${peak}` : ""}</p>
      <div className="flex h-28 items-end gap-[2px]" role="img" aria-label={`Publications per year, ${rows[0].year} to ${rows[rows.length - 1].year}`}>
        {rows.map((r) => (
          <div key={r.year} className="group relative flex-1">
            <div
              className={`w-full rounded-t-sm transition ${r.year === peak ? "bg-nv" : "bg-nv/45 group-hover:bg-nv/80"}`}
              style={{ height: `${Math.max(2, (r.count / max) * 112)}px` }}
            />
            <span className="pointer-events-none absolute -top-7 left-1/2 z-10 hidden -translate-x-1/2 rounded bg-panel-2 px-1.5 py-0.5 font-mono text-[10px] whitespace-nowrap group-hover:block">
              {r.year}: {fmt(r.count)}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted">
        <span>{rows[0].year}</span><span>{rows[rows.length - 1].year}</span>
      </div>
    </section>
  );
}

export default function ResearchPanel({ query }: { query: string }) {
  const [data, setData] = useState<Research | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let live = true;
    setData(null);
    setErr("");
    getResearch(query).then((d) => live && setData(d)).catch((e) => live && setErr((e as Error).message));
    return () => { live = false; };
  }, [query]);

  if (err) return <p className="mt-5 text-sm text-amber-300/90">{err}</p>;
  if (!data)
    return (
      <div className="mt-5 space-y-3">
        <p className="flex items-center gap-2 text-xs text-muted"><Loader2 size={13} className="animate-spin text-nv" /> Mapping the literature on OpenAlex…</p>
        {[0, 1, 2].map((i) => <div key={i} className="shimmer h-20 rounded-xl" />)}
      </div>
    );
  const empty = !data.key_papers.length && !data.foundational.length;
  return (
    <div className="mt-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
        <span className="flex items-center gap-1.5"><BookOpen size={13} className="text-nv" /> <b className="text-text">{fmt(data.total_works)}</b> works on “{data.query}”</span>
        <span>Source: OpenAlex (CC0)</span>
      </div>
      {empty ? (
        <p className="mt-5 text-sm text-muted">No scholarly works found for this topic. Try the Academic focus with different keywords.</p>
      ) : (
        <>
          <Timeline rows={data.timeline} peak={data.peak_year} />
          <Section icon={Sparkles} title="Key papers" hint="Most relevant to your question" papers={data.key_papers} />
          <Section icon={Landmark} title="Foundational" hint="Most-cited works on this topic" papers={data.foundational} />
          <Section icon={Flame} title="Rising" hint="Most-cited from the last two years" papers={data.rising} />
          <Section icon={BookOpen} title="Read next" hint="Related to several of the key papers" papers={data.read_next} />
        </>
      )}
    </div>
  );
}
