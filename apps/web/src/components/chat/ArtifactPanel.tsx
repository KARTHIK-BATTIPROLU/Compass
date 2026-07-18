"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { X, Pencil, Eye } from "lucide-react";
import { useState } from "react";
import { ArtifactRenderer, ArtifactTypeMeta } from "./ArtifactRenderer";

export interface PanelArtifact {
  id: string;
  type: string;
  content: string;
  download_url?: string;
}

interface ArtifactPanelProps {
  artifact: PanelArtifact | null;
  onClose: () => void;
}

const EDITABLE_TYPES = new Set(["script", "flow", "worksheet"]);

export function ArtifactPanel({ artifact, onClose }: ArtifactPanelProps) {
  const reduceMotion = useReducedMotion();
  const [mode, setMode] = useState<"preview" | "edit">("preview");

  const meta = artifact ? ArtifactTypeMeta(artifact.type) : null;
  const editable = artifact ? EDITABLE_TYPES.has(artifact.type) : false;

  return (
    <AnimatePresence>
      {artifact && (
        <>
          <motion.div
            key="scrim"
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
            aria-hidden="true"
          />
          <motion.div
            key="panel"
            role="dialog"
            aria-modal="true"
            aria-label={`${meta?.label ?? "Artifact"} panel`}
            initial={reduceMotion ? false : { x: "100%" }}
            animate={{ x: 0 }}
            exit={reduceMotion ? undefined : { x: "100%" }}
            transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 320, damping: 34 }}
            className="fixed right-0 top-0 h-full w-full sm:w-[460px] lg:w-[520px] z-50 liquid-glass liquid-glass-lg bg-bg-panel border-l border-steel/20 shadow-2xl flex flex-col"
          >
            {/* Sticky header */}
            <div className="shrink-0 flex items-center justify-between gap-3 px-5 py-4 border-b border-steel/15">
              <div className="min-w-0">
                <span
                  className="font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-full border inline-block mb-1.5"
                  style={{ color: meta?.color, borderColor: `color-mix(in srgb, ${meta?.color} 40%, transparent)` }}
                >
                  {meta?.label}
                </span>
                <h2 className="font-display text-lg font-semibold text-white truncate">{meta?.title}</h2>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {editable && (
                  <button
                    type="button"
                    onClick={() => setMode(m => (m === "preview" ? "edit" : "preview"))}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-steel/25 text-steel hover:text-white hover:border-steel/40 transition-colors"
                  >
                    {mode === "preview" ? <><Pencil className="w-3.5 h-3.5" /> Edit</> : <><Eye className="w-3.5 h-3.5" /> Preview</>}
                  </button>
                )}
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close artifact panel"
                  className="p-1.5 rounded-lg text-steel hover:text-white hover:bg-white/5 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-5">
              {mode === "edit" ? (
                <textarea
                  defaultValue={artifact.content}
                  className="w-full h-full min-h-[60vh] bg-black/20 border border-steel/20 rounded-2xl p-4 text-sm text-slate-200 font-mono outline-none focus:border-ember resize-none"
                />
              ) : (
                <ArtifactRenderer content={artifact.content} artifactType={artifact.type} downloadUrl={artifact.download_url} embedded />
              )}
            </div>

            {/* Export bar, pinned bottom */}
            {artifact.download_url && (
              <div className="shrink-0 px-5 py-4 border-t border-steel/15">
                <ExportBar downloadUrl={artifact.download_url} artifactType={artifact.type} />
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function ExportBar({ downloadUrl, artifactType }: { downloadUrl: string; artifactType: string }) {
  const [downloading, setDownloading] = useState(false);
  const filenames: Record<string, string> = {
    slides: "presentation.pptx",
    script: "script.docx",
    worksheet: "worksheet.docx",
    flashcards: "flashcards.csv",
    research_brief: "research_brief.pdf",
    resource_card: "resource_card.pdf",
    flow: "flow.docx",
  };
  const labels: Record<string, string> = {
    slides: "Download PPTX",
    script: "Download DOCX",
    worksheet: "Download DOCX",
    flashcards: "Download CSV",
    research_brief: "Download PDF",
    resource_card: "Download PDF",
    flow: "Download DOCX",
  };

  const handleDownload = async () => {
    try {
      setDownloading(true);
      const { authedFetch } = await import("@/lib/api");
      const res = await authedFetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${downloadUrl}`);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filenames[artifactType] || "export";
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
    <button
      onClick={handleDownload}
      disabled={downloading}
      className="w-full flex items-center justify-center gap-2 bg-ember hover:bg-ember-hot text-bg-deep font-semibold text-sm py-3 rounded-xl transition-colors shadow-lg disabled:opacity-60"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
      {downloading ? "Downloading…" : (labels[artifactType] || "Download")}
    </button>
  );
}
