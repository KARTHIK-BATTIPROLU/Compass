"use client";

import { FileText, Presentation, BookOpen, Layers } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useState } from "react";
import { motion } from "framer-motion";

interface ArtifactRendererProps {
  content: string;
  artifactType?: string; // when passed from structured artifact panel
}

// ── 3D Flashcard ─────────────────────────────────────────────────────────────
const FlashcardItem = ({ front, back }: { front: string; back: string }) => {
  const [flipped, setFlipped] = useState(false);
  return (
    <div
      className="relative w-full h-48 cursor-pointer group"
      style={{ perspective: "1000px" }}
      onClick={() => setFlipped(!flipped)}
    >
      <div
        className="w-full h-full transition-transform duration-500 ease-in-out"
        style={{ transformStyle: "preserve-3d", transform: flipped ? "rotateY(180deg)" : "none" }}
      >
        <div
          className="absolute inset-0 bg-slate-800/90 border border-white/10 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg group-hover:border-white/20 transition-colors"
          style={{ backfaceVisibility: "hidden" }}
        >
          <p className="text-lg font-medium text-slate-200">{front}</p>
        </div>
        <div
          className="absolute inset-0 bg-fuchsia-600/90 border border-fuchsia-400/30 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg"
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
        >
          <p className="text-lg font-medium text-white">{back}</p>
        </div>
      </div>
    </div>
  );
};

// ── Shared section parser (splits by ## headers) ──────────────────────────────
const parseSections = (text: string) =>
  text.split(/(?=\n## )/g).map(s => s.trim()).filter(Boolean);

// ── W-A-S Script renderer ────────────────────────────────────────────────────
function ScriptArtifact({ content }: { content: string }) {
  const [activeTab, setActiveTab] = useState<"weak" | "average" | "strong">("weak");
  const sections = { weak: "", average: "", strong: "" };

  // Try to split on the WEAK/AVERAGE/STRONG headers
  const weakMatch = content.match(/## 🟢 WEAK[^\n]*\n([\s\S]*?)(?=## 🟡 AVERAGE|$)/);
  const avgMatch  = content.match(/## 🟡 AVERAGE[^\n]*\n([\s\S]*?)(?=## 🔴 STRONG|$)/);
  const strMatch  = content.match(/## 🔴 STRONG[^\n]*\n([\s\S]*?)(?=$)/);

  sections.weak    = weakMatch?.[1]?.trim() || content;
  sections.average = avgMatch?.[1]?.trim()  || "";
  sections.strong  = strMatch?.[1]?.trim()  || "";

  const tabs: { key: "weak" | "average" | "strong"; label: string; color: string }[] = [
    { key: "weak",    label: "🟢 Weak",    color: "emerald" },
    { key: "average", label: "🟡 Average",  color: "yellow" },
    { key: "strong",  label: "🔴 Strong",   color: "red" },
  ];

  return (
    <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-3xl overflow-hidden shadow-2xl mt-2">
      <div className="bg-indigo-600/30 border-b border-white/10 px-5 py-4 flex items-center gap-3">
        <FileText className="w-5 h-5 text-indigo-300" />
        <span className="text-sm font-bold text-indigo-100 tracking-widest uppercase">W-A-S Teaching Script</span>
      </div>
      <div className="flex border-b border-white/10">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors ${
              activeTab === tab.key
                ? "bg-white/10 text-white border-b-2 border-indigo-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="p-5">
        <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0">
          <ReactMarkdown>
          {sections[activeTab] || "*No content for this section.*"}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

// ── Slides renderer ───────────────────────────────────────────────────────────
function SlidesArtifact({ content }: { content: string }) {
  const slideRegex = /\n---\n/;
  const rawContent = content.replace(/<artifact[^>]*>/g, "").replace(/<\/artifact>/g, "").trim();
  const slides = rawContent.split(slideRegex).map(s => s.trim()).filter(Boolean);
  const [current, setCurrent] = useState(0);

  return (
    <div className="bg-purple-500/10 border border-purple-500/20 rounded-3xl overflow-hidden shadow-2xl mt-2">
      <div className="bg-purple-600/30 border-b border-white/10 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Presentation className="w-5 h-5 text-purple-300" />
          <span className="text-sm font-bold text-purple-100 tracking-widest uppercase">Presentation</span>
        </div>
        <span className="text-xs text-purple-300 font-mono">{current + 1} / {slides.length}</span>
      </div>
      <div className="p-6 min-h-[180px]">
        <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0 prose-h2:text-purple-200">
          <ReactMarkdown>
          {slides[current] || ""}
          </ReactMarkdown>
        </div>
      </div>
      <div className="flex items-center justify-between px-5 py-3 border-t border-white/10">
        <button
          onClick={() => setCurrent(c => Math.max(0, c - 1))}
          disabled={current === 0}
          className="px-4 py-1.5 text-xs rounded-xl bg-purple-600/30 text-purple-200 disabled:opacity-30 hover:bg-purple-600/50 transition-colors"
        >
          ← Prev
        </button>
        <div className="flex gap-1">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={`w-2 h-2 rounded-full transition-colors ${i === current ? "bg-purple-400" : "bg-white/20"}`}
            />
          ))}
        </div>
        <button
          onClick={() => setCurrent(c => Math.min(slides.length - 1, c + 1))}
          disabled={current === slides.length - 1}
          className="px-4 py-1.5 text-xs rounded-xl bg-purple-600/30 text-purple-200 disabled:opacity-30 hover:bg-purple-600/50 transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

// ── Lecture Flow renderer ─────────────────────────────────────────────────────
function FlowArtifact({ content }: { content: string }) {
  const rawContent = content.replace(/<artifact[^>]*>/g, "").replace(/<\/artifact>/g, "").trim();
  return (
    <div className="bg-teal-500/10 border border-teal-500/20 rounded-3xl overflow-hidden shadow-2xl mt-2">
      <div className="bg-teal-600/30 border-b border-white/10 px-5 py-4 flex items-center gap-3">
        <Layers className="w-5 h-5 text-teal-300" />
        <span className="text-sm font-bold text-teal-100 tracking-widest uppercase">Lecture Flow</span>
      </div>
      <div className="p-5">
        <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-0 prose-h2:text-teal-200 prose-h3:text-teal-300">
          <ReactMarkdown>
          {rawContent}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

// ── Main Renderer ─────────────────────────────────────────────────────────────
export function ArtifactRenderer({ content, artifactType }: ArtifactRendererProps) {
  // If an explicit type is passed from the structured artifact panel, use it directly
  if (artifactType === "slides") return <SlidesArtifact content={content} />;
  if (artifactType === "script") return <ScriptArtifact content={content} />;
  if (artifactType === "flow")   return <FlowArtifact content={content} />;

  // ── Regex-based detection for inline artifact tags (streamed content) ───────
  const slideMatch        = content.match(/<artifact type="slides">([\s\S]*?)<\/artifact>/);
  const scriptMatch       = content.match(/<artifact type="script">([\s\S]*?)<\/artifact>/);
  const flowMatch         = content.match(/<artifact type="flow">([\s\S]*?)<\/artifact>/);
  const quizMatch         = content.match(/<artifact type="quiz_link" token="([^"]+)">([\s\S]*?)<\/artifact>/);
  const worksheetMatch    = content.match(/<artifact type="worksheet">([\s\S]*?)<\/artifact>/);
  const researchMatch     = content.match(/<artifact type="research_brief">([\s\S]*?)<\/artifact>/);
  const resourceMatch     = content.match(/<artifact type="resource_card">([\s\S]*?)<\/artifact>/);
  const diagramMatch      = content.match(/<artifact type="diagram_gallery">([\s\S]*?)<\/artifact>/);
  const flashcardsMatch   = content.match(/<artifact type="flashcards">([\s\S]*?)<\/artifact>/);

  if (slideMatch)  return <SlidesArtifact content={slideMatch[1].trim()} />;
  if (scriptMatch) return <ScriptArtifact content={scriptMatch[1].trim()} />;
  if (flowMatch)   return <FlowArtifact content={flowMatch[1].trim()} />;

  if (quizMatch) {
    const token = quizMatch[1];
    return (
      <div className="bg-emerald-500/10 border border-emerald-500/20 p-6 rounded-3xl shadow-xl mt-4">
        <h3 className="text-emerald-300 font-bold mb-2 flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          Live Quiz Ready!
        </h3>
        <p className="text-sm text-slate-300 mb-4">Share this link with your students. Results will appear here automatically.</p>
        <a href={`/q/${token}`} target="_blank"
          className="text-emerald-400 underline font-mono bg-black/20 p-2 rounded-lg block w-fit hover:bg-black/40 transition-colors">
          {typeof window !== "undefined" ? window.location.origin : "http://localhost:3000"}/q/{token}
        </a>
      </div>
    );
  }

  if (worksheetMatch) {
    return (
      <div className="bg-blue-500/10 border border-blue-500/20 p-6 rounded-3xl shadow-xl mt-4">
        <div className="flex justify-between items-center mb-4 border-b border-blue-500/20 pb-4">
          <h3 className="text-blue-300 font-bold flex items-center gap-2">
            <FileText className="w-5 h-5" /> Printable Worksheet
          </h3>
          <button onClick={() => window.print()}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors shadow-lg">
            Print to PDF
          </button>
        </div>
        <div className="prose prose-invert prose-blue max-w-none prose-sm print:prose-black">
          <ReactMarkdown>{worksheetMatch[1].trim()}</ReactMarkdown>
        </div>
      </div>
    );
  }

  if (researchMatch) {
    try {
      const data = JSON.parse(researchMatch[1].trim());
      return (
        <div className="bg-amber-500/10 border border-amber-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-amber-300 font-bold mb-4 text-xl">Update & Research: {data.title}</h3>
          <div className="prose prose-invert prose-amber max-w-none prose-sm mb-6">
            <ReactMarkdown>{data.brief_markdown}</ReactMarkdown>
          </div>
          {data.citations?.length > 0 && (
            <div className="border-t border-amber-500/20 pt-4">
              <h4 className="text-amber-400 font-semibold mb-2 text-xs uppercase tracking-wider">Citations</h4>
              <ul className="space-y-2 text-sm text-slate-300">
                {data.citations.map((c: any, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-amber-500 font-mono">[{c.id}]</span>
                    <a href={c.url} target="_blank" className="hover:text-amber-300 underline break-all">{c.title}</a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    } catch { return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl">Error parsing research brief.</div>; }
  }

  if (resourceMatch) {
    try {
      const data = JSON.parse(resourceMatch[1].trim());
      const [tab, setTab] = useState<"news" | "papers" | "docs">("news");
      return (
        <div className="bg-cyan-500/10 border border-cyan-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-cyan-300 font-bold mb-4 text-xl">Resource Card</h3>
          <div className="flex gap-1 mb-4">
            {(["news", "papers", "docs"] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${tab === t ? "bg-cyan-500/30 text-cyan-200" : "text-slate-400 hover:text-slate-200"}`}>
                {t}
              </button>
            ))}
          </div>
          <div className="space-y-3 mb-6 max-h-60 overflow-y-auto pr-1">
            {(data[tab] || []).map((item: any, i: number) => (
              <a key={i} href={item.url} target="_blank"
                className="block bg-black/20 rounded-xl p-3 hover:bg-black/40 transition-colors">
                <p className="text-sm text-slate-200 font-medium">{item.title}</p>
                <p className="text-xs text-slate-400 truncate mt-1">{item.url}</p>
              </a>
            ))}
          </div>
          <div className="prose prose-invert prose-cyan max-w-none prose-sm border-t border-cyan-500/20 pt-4">
            <ReactMarkdown>{data.synthesis_markdown}</ReactMarkdown>
          </div>
        </div>
      );
    } catch { return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl">Error parsing resource card.</div>; }
  }

  if (diagramMatch) {
    try {
      const data = JSON.parse(diagramMatch[1].trim());
      return (
        <div className="bg-pink-500/10 border border-pink-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-pink-300 font-bold mb-4 text-xl">Diagram Gallery</h3>
          <div className="space-y-6">
            {data.images?.map((img: any, i: number) => (
              <div key={i} className="bg-black/30 rounded-2xl overflow-hidden border border-white/5">
                <img src={img.url} alt={img.title} className="w-full max-h-64 object-contain bg-slate-950 p-2" />
                <div className="p-4">
                  <a href={img.source_url} target="_blank" className="text-xs text-pink-400 hover:underline block mb-2 font-mono truncate">
                    {img.license ? `© ${img.license}` : "Source"}: {img.title}
                  </a>
                  {img.breakdown && <p className="text-sm text-slate-300">{img.breakdown}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    } catch { return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl">Error parsing diagrams.</div>; }
  }

  if (flashcardsMatch) {
    try {
      const data = JSON.parse(flashcardsMatch[1].trim());
      return (
        <div className="bg-fuchsia-500/10 border border-fuchsia-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-fuchsia-300 font-bold mb-6 text-xl text-center uppercase tracking-wide">
            Flashcards: {data.title}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.cards?.map((card: any, i: number) => (
              <FlashcardItem key={i} front={card.front} back={card.back} />
            ))}
          </div>
          <p className="text-center mt-6 text-xs text-fuchsia-400/50 uppercase tracking-widest">Click to flip</p>
        </div>
      );
    } catch { return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl">Error parsing flashcards.</div>; }
  }

  // Default: plain markdown
  return (
    <div className="prose prose-invert max-w-none prose-sm text-slate-300 prose-headings:mt-2 prose-p:leading-relaxed">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
