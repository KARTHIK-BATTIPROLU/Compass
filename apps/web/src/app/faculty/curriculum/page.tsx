"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { createClient } from "@/utils/supabase/client";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface CurriculumFile {
  id: string;
  filename: string;
  topic: string;
  chunk_count: number;
  created_at: string;
}

export default function CurriculumUploadPage() {
  const [files, setFiles] = useState<CurriculumFile[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [topic, setTopic] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    try {
      const { authedFetch } = await import("@/lib/api");
      const res = await authedFetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/curriculum/files`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch (e) {
      console.error("Failed to load curriculum files", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const acceptFile = (file: File | null | undefined) => {
    if (!file) return;
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setUploadStatus("error");
      setErrorMessage("Only PDF or DOCX files are supported.");
      return;
    }
    setSelectedFile(file);
    setUploadStatus("idle");
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !topic.trim()) return;

    setUploading(true);
    setUploadStatus("idle");
    setErrorMessage("");

    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      setUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("topic", topic.trim());

    try {
      const { authedFetch } = await import("@/lib/api");
      const res = await authedFetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/curriculum/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload failed");
      }

      setUploadStatus("success");
      setSelectedFile(null);
      setTopic("");
      if (fileInputRef.current) fileInputRef.current.value = "";

      loadFiles();

      setTimeout(() => setUploadStatus("idle"), 3000);
    } catch (e: any) {
      console.error("Upload error:", e);
      setUploadStatus("error");
      setErrorMessage(e.message || "Something went wrong processing this document — try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen platform-mesh platform-mesh-faculty text-white p-6 md:p-10">
      <div className="relative z-10 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10">

        {/* Upload Form */}
        <div className="space-y-6">
          <div>
            <h1 className="font-display text-3xl font-semibold text-slate-100">Upload curriculum</h1>
            <p className="text-steel mt-1">
              Add syllabi, textbooks, or notes. LearnForge chunks and indexes them so lesson generation stays aligned to your class.
            </p>
          </div>

          <form onSubmit={handleUpload} className="liquid-glass liquid-glass-lg bg-bg-panel border border-steel/20 rounded-3xl p-6 md:p-8 shadow-2xl">
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-steel mb-2 uppercase tracking-wide font-mono">
                  Topic / Subject
                </label>
                <input
                  type="text"
                  required
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. AP Biology Unit 1"
                  className="w-full bg-black/20 border border-steel/25 focus:border-ember rounded-xl px-4 py-3 text-white outline-none transition-colors placeholder:text-steel/50"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-steel mb-2 uppercase tracking-wide font-mono">
                  Document (PDF, DOCX)
                </label>
                {/* The anvil — where raw material (a syllabus) lands before being forged */}
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragActive(false);
                    acceptFile(e.dataTransfer.files?.[0]);
                  }}
                  className={`liquid-glass liquid-glass-sm border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
                    dragActive
                      ? "border-ember bg-ember/10 ember-glow"
                      : selectedFile
                      ? "border-ember/50 bg-ember/5"
                      : "border-steel/25 hover:border-steel/40 hover:bg-white/5"
                  }`}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".pdf,.docx"
                    required
                    onChange={(e) => acceptFile(e.target.files?.[0])}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                    {selectedFile ? (
                      <>
                        <FileText className="w-10 h-10 text-ember mb-3" />
                        <span className="text-sm font-medium text-slate-200">{selectedFile.name}</span>
                        <span className="text-xs text-steel mt-1 font-mono">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-10 h-10 text-steel mb-3" />
                        <span className="text-sm font-medium text-slate-300">Drop a file here, or click to browse</span>
                        <span className="text-xs text-steel mt-1">PDF or DOCX, up to 20MB</span>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={!selectedFile || !topic.trim() || uploading}
                className="w-full bg-ember hover:bg-ember-hot disabled:bg-white/5 disabled:text-steel/50 text-bg-deep font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing and indexing…
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload and index
                  </>
                )}
              </button>

              {uploadStatus === "success" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-mint/10 border border-mint/25 rounded-xl flex items-center gap-3 text-emerald-200 text-sm">
                  <CheckCircle2 className="w-5 h-5 text-mint shrink-0" />
                  Indexed successfully — ready for lesson generation.
                </motion.div>
              )}

              {uploadStatus === "error" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-red-500/10 border border-red-500/25 rounded-xl flex items-center gap-3 text-red-200 text-sm">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  {errorMessage}
                </motion.div>
              )}
            </div>
          </form>
        </div>

        {/* Uploaded Files List */}
        <div className="space-y-6">
          <div>
            <h2 className="font-display text-2xl font-semibold text-slate-100">Indexed library</h2>
            <p className="text-steel mt-1">Documents available to the retrieval engine.</p>
          </div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="skeleton-shimmer h-20 rounded-2xl border border-steel/15" />
              ))}
            </div>
          ) : files.length === 0 ? (
            <div className="liquid-glass bg-bg-panel border border-steel/20 rounded-3xl p-12 text-center flex flex-col items-center">
              <FileText className="w-12 h-12 text-steel/50 mb-4" />
              <h3 className="font-display text-lg font-medium text-slate-300">Library is empty</h3>
              <p className="text-sm text-steel mt-1">Upload a document and it&apos;ll appear here.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {files.map((f, i) => (
                <motion.div
                  key={f.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="liquid-glass liquid-glass-sm bg-bg-panel border border-steel/20 rounded-2xl p-4 flex items-start gap-4"
                >
                  <div className="w-10 h-10 rounded-xl bg-ember/15 border border-ember/25 flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-ember" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{f.filename}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-steel">
                      <span className="px-2 py-0.5 bg-white/5 border border-steel/15 rounded text-steel font-medium truncate max-w-[120px]">
                        {f.topic}
                      </span>
                      <span className="font-mono">{f.chunk_count} chunks</span>
                    </div>
                  </div>
                  <div className="text-xs text-steel/70 shrink-0 mt-1 font-mono">
                    {new Date(f.created_at).toLocaleDateString()}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
