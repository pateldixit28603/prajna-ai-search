import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Source } from "../lib/api";

/** Turn "[3]" citations into markdown links so we can render them as chips. */
function linkCitations(md: string) {
  return md.replace(/\[(\d{1,2})\](?!\()/g, "[$1](#cite-$1)");
}

export default function Answer({ text, sources, streaming, dir }: {
  text: string; sources: Source[]; streaming: boolean; dir?: "ltr" | "rtl";
}) {
  const byN = new Map(sources.map((s) => [String(s.n), s]));
  return (
    <div dir={dir ?? "auto"} className={`prose-answer ${streaming ? "caret" : ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href, children }) {
            const m = href?.match(/^#cite-(\d+)$/);
            if (m) {
              const s = byN.get(m[1]);
              if (!s) return <span className="cite">{m[1]}</span>;
              return (
                <a className="cite" href={s.url} target="_blank" rel="noreferrer" title={`${s.title} — ${s.domain}`}>
                  {m[1]}
                </a>
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
    </div>
  );
}
