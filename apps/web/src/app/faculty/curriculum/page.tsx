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
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/curriculum/files?user_id=${user.id}`);
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
    formData.append("user_id", user.id);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/curriculum/upload`, {
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
      
      // Reload list
      loadFiles();
      
      setTimeout(() => setUploadStatus("idle"), 3000);
    } catch (e: any) {
      console.error("Upload error:", e);
      setUploadStatus("error");
      setErrorMessage(e.message || "Failed to process document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 md:p-10">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="relative z-10 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10">
        
        {/* Upload Form */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-100">Upload Curriculum</h1>
            <p className="text-slate-400 mt-1">
              Add syllabi, textbooks, or notes. LearnForge will chunk and vector-index them so your lesson generation is perfectly aligned.
            </p>
          </div>

          <form onSubmit={handleUpload} className="bg-slate-800/40 border border-white/10 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl">
            
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                  Topic / Subject
                </label>
                <input
                  type="text"
                  required
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. AP Biology Unit 1"
                  className="w-full bg-slate-900/60 border border-slate-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-white outline-none transition-colors placeholder:text-slate-600"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                  Document (PDF, DOCX)
                </label>
                <div 
                  className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
                    selectedFile ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-slate-700 hover:border-slate-500 hover:bg-white/5'
                  }`}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".pdf,.docx"
                    required
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                    {selectedFile ? (
                      <>
                        <FileText className="w-10 h-10 text-indigo-400 mb-3" />
                        <span className="text-sm font-medium text-slate-200">{selectedFile.name}</span>
                        <span className="text-xs text-slate-500 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-10 h-10 text-slate-500 mb-3" />
                        <span className="text-sm font-medium text-slate-300">Click to browse or drag and drop</span>
                        <span className="text-xs text-slate-500 mt-1">PDF or DOCX (Max 20MB)</span>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={!selectedFile || !topic.trim() || uploading}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing & Indexing...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload & Index
                  </>
                )}
              </button>

              {uploadStatus === "success" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-300 text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  Successfully indexed to Qdrant!
                </motion.div>
              )}

              {uploadStatus === "error" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-300 text-sm">
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
            <h2 className="text-2xl font-bold text-slate-100">Indexed Library</h2>
            <p className="text-slate-400 mt-1">Documents available to the LearnForge RAG engine.</p>
          </div>

          {loading ? (
             <div className="flex justify-center p-12">
               <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
             </div>
          ) : files.length === 0 ? (
            <div className="bg-slate-800/40 border border-white/10 rounded-3xl p-12 text-center flex flex-col items-center">
              <FileText className="w-12 h-12 text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-300">Library is empty</h3>
              <p className="text-sm text-slate-500 mt-1">Upload a document to build your knowledge base.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {files.map((f, i) => (
                <motion.div 
                  key={f.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-slate-800/40 border border-white/10 rounded-2xl p-4 flex items-start gap-4 backdrop-blur-md"
                >
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-indigo-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{f.filename}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                      <span className="px-2 py-0.5 bg-slate-700/50 rounded text-slate-300 font-medium truncate max-w-[120px]">
                        {f.topic}
                      </span>
                      <span>{f.chunk_count} chunks</span>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 shrink-0 mt-1">
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
