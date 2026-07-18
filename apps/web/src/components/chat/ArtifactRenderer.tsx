"use client";

import { FileText, Presentation, Layers } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useState } from "react";

interface ArtifactRendererProps {
  content: string;
  artifactType?: string; // when set, this is a discrete artifact from the structured `artifacts` list
  downloadUrl?: string;
  embedded?: boolean; // true inside ArtifactPanel — suppress the card's own header/export chrome
}

const TYPE_META: Record<string, { label: string; title: string; color: string }> = {
  slides: { label: "Presentation", title: "Presentation", color: "var(--ember)" },
  script: { label: "W-A-S Script", title: "Teaching Script", color: "var(--ember)" },
  flow: { label: "Lecture Flow", title: "Lecture Flow", color: "var(--ember)" },
  quiz: { label: "Quiz", title: "Quiz", color: "var(--mint-signal)" },
  worksheet: { label: "Worksheet", title: "Printable Worksheet", color: "var(--ember)" },
  research_brief: { label: "Research Brief", title: "Update & Research", color: "var(--ember)" },
  resource_card: { label: "Resource Card", title: "Resource Card", color: "var(--mint-signal)" },
  diagram_gallery: { label: "Diagrams", title: "Diagram Gallery", color: "var(--mint-signal)" },
  flashcards: { label: "Flashcards", title: "Flashcards", color: "var(--mint-signal)" },
};

export function ArtifactTypeMeta(type: string) {
  return TYPE_META[type] || { label: "Artifact", title: "Artifact", color: "var(--steel)" };
}

function DownloadButton({ url, filename, label, className }: { url: string; filename: string; label: string; className: string }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setDownloading(true);
      const { authedFetch } = await import("@/lib/api");
      const res = await authedFetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${url}`);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (e) {
      console.error("Download error", e);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <button onClick={handleDownload} disabled={downloading} className={className}>
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
      {downloading ? "Downloading…" : label}
    </button>
  );
}

// ── 3D Flashcard ─────────────────────────────────────────────────────────────
const FlashcardItem = ({ front, back }: { front: string; back: string }) => {
  const [flipped, setFlipped] = useState(false);
  return (
    <div
      className="relative w-full h-48 cursor-pointer group"
      style={{ perspective: "1000px" }}
      onClick={() => setFlipped(!flipped)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setFlipped(!flipped); }}
      aria-label="Flip flashcard"
    >
      <div
        className="w-full h-full transition-transform duration-500 ease-in-out motion-reduce:transition-none"
        style={{ transformStyle: "preserve-3d", transform: flipped ? "rotateY(180deg)" : "none" }}
      >
        <div
          className="absolute inset-0 bg-bg-panel border border-steel/20 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg group-hover:border-steel/35 transition-colors"
          style={{ backfaceVisibility: "hidden" }}
        >
          <p className="text-lg font-medium text-slate-200">{front}</p>
        </div>
        <div
          className="absolute inset-0 bg-ember/90 border border-ember-hot/40 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg"
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
        >
          <p className="text-lg font-medium text-bg-deep">{back}</p>
        </div>
      </div>
    </div>
  );
};

// ── W-A-S Script renderer — carries the signature seam ────────────────────────
function ScriptArtifact({ content, embedded }: { content: string; embedded?: boolean }) {
  const [open, setOpen] = useState<{ weak: boolean; average: boolean; strong: boolean }>({ weak: true, average: true, strong: true });

  const weakMatch = content.match(/## 🟢 WEAK[^\n]*\n([\s\S]*?)(?=## 🟡 AVERAGE|$)/);
  const avgMatch  = content.match(/## 🟡 AVERAGE[^\n]*\n([\s\S]*?)(?=## 🔴 STRONG|$)/);
  const strMatch  = content.match(/## 🔴 STRONG[^\n]*\n([\s\S]*?)(?=$)/);

  const sections = [
    { key: "weak" as const, label: "Weak — Foundational", color: "var(--mint-signal)", body: weakMatch?.[1]?.trim() || (avgMatch || strMatch ? "" : content) },
    { key: "average" as const, label: "Average — Standard", color: "var(--ember)", body: avgMatch?.[1]?.trim() || "" },
    { key: "strong" as const, label: "Strong — Advanced", color: "var(--ember-deep)", body: strMatch?.[1]?.trim() || "" },
  ].filter(s => s.body);

  return (
    <div className={embedded ? "" : "liquid-glass bg-bg-panel border border-steel/20 rounded-3xl overflow-hidden shadow-2xl mt-2"}>
      <div className="flex flex-col divide-y divide-steel/10">
        {sections.map(s => (
          <div key={s.key} className="flex">
            <div className="was-seam w-[3px] shrink-0" style={{ background: s.color }} aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <button
                type="button"
                onClick={() => setOpen(o => ({ ...o, [s.key]: !o[s.key] }))}
                className="w-full flex items-center justify-between px-4 py-3 text-left"
              >
                <span className="text-xs font-mono uppercase tracking-widest" style={{ color: s.color }}>{s.label}</span>
                <span className="text-steel text-xs">{open[s.key] ? "−" : "+"}</span>
              </button>
              {open[s.key] && (
                <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0 px-4 pb-4">
                  <ReactMarkdown>{s.body}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Slides renderer ───────────────────────────────────────────────────────────
function SlidesArtifact({ content, embedded }: { content: string; embedded?: boolean }) {
  const slideRegex = /\n---\n/;
  const rawContent = content.replace(/<artifact[^>]*>/g, "").replace(/<\/artifact>/g, "").trim();
  const slides = rawContent.split(slideRegex).map(s => s.trim()).filter(Boolean);
  const [current, setCurrent] = useState(0);

  return (
    <div className={embedded ? "" : "liquid-glass bg-bg-panel border border-steel/20 rounded-3xl overflow-hidden shadow-2xl mt-2"}>
      <div className="p-6 min-h-[180px] bg-black/10 rounded-2xl border border-steel/15">
        <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0 prose-h2:text-ember">
          <ReactMarkdown>{slides[current] || ""}</ReactMarkdown>
        </div>
      </div>
      <div className="flex items-center justify-between px-1 py-3">
        <button
          onClick={() => setCurrent(c => Math.max(0, c - 1))}
          disabled={current === 0}
          className="px-4 py-1.5 text-xs rounded-xl border border-steel/25 text-steel disabled:opacity-30 hover:text-white hover:border-steel/40 transition-colors"
        >
          ← Prev
        </button>
        <span className="text-xs text-steel font-mono">{current + 1} / {slides.length}</span>
        <button
          onClick={() => setCurrent(c => Math.min(slides.length - 1, c + 1))}
          disabled={current === slides.length - 1}
          className="px-4 py-1.5 text-xs rounded-xl border border-steel/25 text-steel disabled:opacity-30 hover:text-white hover:border-steel/40 transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

// ── Lecture Flow renderer ─────────────────────────────────────────────────────
function FlowArtifact({ content, embedded }: { content: string; embedded?: boolean }) {
  const rawContent = content.replace(/<artifact[^>]*>/g, "").replace(/<\/artifact>/g, "").trim();
  return (
    <div className={embedded ? "" : "liquid-glass bg-bg-panel border border-steel/20 rounded-3xl overflow-hidden shadow-2xl mt-2 p-5"}>
      <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0 prose-h2:text-ember prose-h3:text-ember-hot">
        <ReactMarkdown>{rawContent}</ReactMarkdown>
      </div>
    </div>
  );
}

// Strip <artifact>...</artifact> blocks from raw streamed text, leaving only
// surrounding prose. Discrete artifacts render once, from the structured
// `artifacts` list (passed with an explicit artifactType) — not from here too.
function stripArtifactTags(text: string): string {
  return text.replace(/<artifact[^>]*>[\s\S]*?<\/artifact>/g, "").trim();
}

// ── Main Renderer ─────────────────────────────────────────────────────────────
export function ArtifactRenderer({ content, artifactType, downloadUrl, embedded }: ArtifactRendererProps) {
  // No explicit type => this is the raw streaming message text, not a
  // discrete artifact card. Strip any artifact tags (rendered separately,
  // once, via the structured artifacts list) and show only the prose.
  if (!artifactType) {
    const prose = stripArtifactTags(content);
    if (!prose) return null;
    return (
      <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-2 prose-p:leading-relaxed">
        <ReactMarkdown>{prose}</ReactMarkdown>
      </div>
    );
  }

  if (artifactType === "slides") return <SlidesArtifact content={content} embedded={embedded} />;
  if (artifactType === "script") return <ScriptArtifact content={content} embedded={embedded} />;
  if (artifactType === "flow")   return <FlowArtifact content={content} embedded={embedded} />;

  const quizMatch      = content.match(/<artifact type="quiz_link" token="([^"]+)">([\s\S]*?)<\/artifact>/);
  const worksheetMatch = content.match(/<artifact type="worksheet">([\s\S]*?)<\/artifact>/);
  const researchMatch  = content.match(/<artifact type="research_brief">([\s\S]*?)<\/artifact>/);
  const resourceMatch  = content.match(/<artifact type="resource_card">([\s\S]*?)<\/artifact>/);
  const diagramMatch   = content.match(/<artifact type="diagram_gallery">([\s\S]*?)<\/artifact>/);
  const flashcardsMatch = content.match(/<artifact type="flashcards">([\s\S]*?)<\/artifact>/);

  const cardClass = embedded ? "" : "liquid-glass bg-bg-panel border border-steel/20 p-6 rounded-3xl shadow-xl mt-4";

  if (quizMatch) {
    const token = quizMatch[1];
    return (
      <div className={cardClass}>
        <h3 className="text-mint font-semibold mb-2 flex items-center gap-2 font-display text-lg">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mint opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-mint"></span>
          </span>
          Live quiz ready
        </h3>
        <p className="text-sm text-steel mb-4">Share this link with your students. Results appear here automatically.</p>
        <a href={`/q/${token}`} target="_blank"
          className="text-mint underline font-mono text-sm bg-black/20 p-2.5 rounded-lg block w-fit hover:bg-black/35 transition-colors break-all">
          {typeof window !== "undefined" ? window.location.origin : ""}/q/{token}
        </a>
      </div>
    );
  }

  if (worksheetMatch) {
    return (
      <div className={cardClass}>
        {!embedded && (
          <div className="flex justify-between items-center mb-4 border-b border-steel/15 pb-4">
            <h3 className="text-white font-display font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-ember" /> Printable Worksheet
            </h3>
            <button onClick={() => window.print()}
              className="bg-white/5 border border-steel/25 hover:border-steel/40 text-steel hover:text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors">
              Print to PDF
            </button>
          </div>
        )}
        <div className="prose prose-invert max-w-none prose-sm print:prose-black">
          <ReactMarkdown>{worksheetMatch[1].trim()}</ReactMarkdown>
        </div>
      </div>
    );
  }

  if (researchMatch) {
    try {
      const data = JSON.parse(researchMatch[1].trim());
      return (
        <div className={cardClass}>
          {!embedded && <h3 className="text-white font-display font-semibold text-xl mb-4">{data.title}</h3>}
          <div className="prose prose-invert max-w-none prose-sm mb-6">
            <ReactMarkdown>{data.brief_markdown}</ReactMarkdown>
          </div>
          {data.citations?.length > 0 && (
            <div className="border-t border-steel/15 pt-4">
              <h4 className="text-steel font-mono font-semibold mb-2 text-xs uppercase tracking-wider">Citations</h4>
              <ul className="space-y-2 text-sm text-slate-300">
                {data.citations.map((c: any, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-ember font-mono text-xs mt-0.5">[{c.id}]</span>
                    <a href={c.url} target="_blank" className="hover:text-ember-hot underline break-all">{c.title}</a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    } catch { return <div className="text-red-300 p-4 border border-red-500/20 rounded-xl">Something went wrong rendering this research brief — try regenerating it.</div>; }
  }

  if (resourceMatch) {
    try {
      const data = JSON.parse(resourceMatch[1].trim());
      return <ResourceCardBody data={data} embedded={embedded} />;
    } catch { return <div className="text-red-300 p-4 border border-red-500/20 rounded-xl">Something went wrong rendering this resource card — try regenerating it.</div>; }
  }

  if (diagramMatch) {
    try {
      const data = JSON.parse(diagramMatch[1].trim());
      return (
        <div className={cardClass}>
          <div className="space-y-6">
            {data.images?.map((img: any, i: number) => (
              <div key={i} className="liquid-glass liquid-glass-sm bg-black/20 rounded-2xl overflow-hidden border border-steel/15">
                <img src={img.url} alt={img.title} className="w-full max-h-64 object-contain bg-bg-deep p-2" />
                <div className="p-4">
                  <a href={img.source_url} target="_blank" className="text-xs text-mint hover:underline block mb-2 font-mono truncate">
                    {img.license ? `© ${img.license}` : "Source"}: {img.title}
                  </a>
                  {img.breakdown && <p className="text-sm text-slate-300">{img.breakdown}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    } catch { return <div className="text-red-300 p-4 border border-red-500/20 rounded-xl">Something went wrong rendering these diagrams — try regenerating them.</div>; }
  }

  if (flashcardsMatch) {
    try {
      const data = JSON.parse(flashcardsMatch[1].trim());
      return (
        <div className={cardClass}>
          {!embedded && <h3 className="text-white font-display font-semibold text-lg mb-6 text-center">{data.title}</h3>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.cards?.map((card: any, i: number) => (
              <FlashcardItem key={i} front={card.front} back={card.back} />
            ))}
          </div>
          <p className="text-center mt-6 text-xs text-steel/70 uppercase tracking-widest font-mono">Click to flip</p>
        </div>
      );
    } catch { return <div className="text-red-300 p-4 border border-red-500/20 rounded-xl">Something went wrong rendering these flashcards — try regenerating them.</div>; }
  }

  // Fallback: unrecognized artifact type — show raw markdown
  return (
    <div className="prose prose-invert max-w-none prose-sm text-slate-300">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}

function ResourceCardBody({ data, embedded }: { data: any; embedded?: boolean }) {
  const [tab, setTab] = useState<"news" | "papers" | "docs">("news");
  return (
    <div className={embedded ? "" : "liquid-glass bg-bg-panel border border-steel/20 p-6 rounded-3xl shadow-xl mt-4"}>
      <div className="flex gap-1 mb-4">
        {(["news", "papers", "docs"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${tab === t ? "bg-mint/15 text-mint" : "text-steel hover:text-slate-200"}`}>
            {t}
          </button>
        ))}
      </div>
      <div className="space-y-3 mb-6 max-h-60 overflow-y-auto pr-1">
        {(data[tab] || []).length === 0 && (
          <p className="text-xs text-steel/70 py-4 text-center">No {tab} sources found for this topic.</p>
        )}
        {(data[tab] || []).map((item: any, i: number) => (
          <a key={i} href={item.url} target="_blank"
            className="liquid-glass liquid-glass-sm block bg-black/20 rounded-xl p-3 hover:bg-black/35 transition-colors border border-steel/10">
            <p className="text-sm text-slate-200 font-medium">{item.title}</p>
            <p className="text-xs text-steel truncate mt-1">{item.url}</p>
          </a>
        ))}
      </div>
      <div className="prose prose-invert max-w-none prose-sm border-t border-steel/15 pt-4">
        <ReactMarkdown>{data.synthesis_markdown}</ReactMarkdown>
      </div>
      {data.citations?.length > 0 && (
        <div className="border-t border-steel/15 pt-4 mt-4">
          <h4 className="text-steel font-mono font-semibold mb-2 text-xs uppercase tracking-wider">Citations</h4>
          <ul className="space-y-2 text-sm text-slate-300">
            {data.citations.map((c: any, i: number) => {
              let domain = "";
              try { domain = new URL(c.url).hostname; } catch {}
              return (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-mint font-mono text-xs mt-0.5">[{c.id}]</span>
                  {domain && (
                    <img src={`https://www.google.com/s2/favicons?domain=${domain}&sz=16`} alt="" className="w-4 h-4 mt-0.5 opacity-70" />
                  )}
                  <a href={c.url} target="_blank" className="hover:text-mint underline break-all">{c.title}</a>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
