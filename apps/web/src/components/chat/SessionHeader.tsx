"use client";

import { User, Database } from "lucide-react";
import { useEffect, useState } from "react";

interface SessionHeaderProps {
  role: "faculty" | "learner";
  contextInfo: {
    classLevel?: string;
    language?: string;
    standard?: string;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function SessionHeader({ role, contextInfo }: SessionHeaderProps) {
  const [qdrantOk, setQdrantOk] = useState(false);

  useEffect(() => {
    if (role === 'faculty') {
      fetch(`${API_BASE}/api/health/qdrant`)
        .then(res => res.json())
        .then(data => setQdrantOk(data.status === 'ok'))
        .catch(() => setQdrantOk(false));
    }
  }, [role]);

  const accent = role === "faculty" ? "ember" : "mint";

  return (
    <div className="liquid-glass liquid-glass-sm h-16 border-b border-steel/10 bg-bg-panel flex items-center justify-between px-4 md:px-6 pl-16 md:pl-6 z-20 relative">
      <div className="flex items-center gap-3 text-white font-medium min-w-0">
        <div className={`p-1.5 rounded-lg bg-${accent}/15 shrink-0`}>
          <User className={`w-4 h-4 text-${accent}`} />
        </div>
        <span className="font-display text-sm font-semibold tracking-wide truncate">{role === 'faculty' ? 'Faculty Workspace' : 'Learner Workspace'}</span>
      </div>

      <div className="flex gap-2 items-center shrink-0">
        {role === 'faculty' && (
           <div className={`hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono uppercase tracking-widest border ${qdrantOk ? 'bg-mint/10 text-mint border-mint/25' : 'bg-red-500/10 text-red-300 border-red-500/25'}`}>
             <Database className="w-3.5 h-3.5" />
             <span>Curriculum: {qdrantOk ? 'Connected' : 'Offline'}</span>
           </div>
        )}
        {role === 'faculty' && contextInfo.classLevel && (
          <span className="px-3 py-1 bg-white/5 text-steel border border-steel/20 rounded-full text-xs font-mono uppercase tracking-widest">
            {contextInfo.classLevel}
          </span>
        )}
        {role === 'faculty' && contextInfo.language && (
          <span className="px-3 py-1 bg-white/5 text-steel border border-steel/20 rounded-full text-xs font-medium">
            {contextInfo.language}
          </span>
        )}
        {role === 'learner' && contextInfo.standard && (
          <span className="px-3 py-1 bg-white/5 text-steel border border-steel/20 rounded-full text-xs font-mono uppercase tracking-widest">
            {contextInfo.standard}
          </span>
        )}
      </div>
    </div>
  )
}
