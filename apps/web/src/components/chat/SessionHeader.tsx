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

export function SessionHeader({ role, contextInfo }: SessionHeaderProps) {
  const [qdrantOk, setQdrantOk] = useState(false);

  useEffect(() => {
    if (role === 'faculty') {
      fetch('http://localhost:8000/api/health/qdrant')
        .then(res => res.json())
        .then(data => setQdrantOk(data.status === 'ok'))
        .catch(() => setQdrantOk(false));
    }
  }, [role]);

  return (
    <div className="h-16 border-b border-white/5 bg-slate-900/30 backdrop-blur-md flex items-center justify-between px-6 z-20 relative">
      <div className="flex items-center gap-3 text-white font-medium">
        <div className={`p-1.5 rounded-lg ${role === 'faculty' ? 'bg-indigo-500/20' : 'bg-violet-500/20'}`}>
          <User className={`w-4 h-4 ${role === 'faculty' ? 'text-indigo-400' : 'text-violet-400'}`} />
        </div>
        <span className="text-sm font-semibold tracking-wide">{role === 'faculty' ? 'Faculty Workspace' : 'Learner Workspace'}</span>
      </div>
      
      <div className="flex gap-2 items-center">
        {role === 'faculty' && (
           <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border ${qdrantOk ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm' : 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-sm'}`}>
             <Database className="w-3.5 h-3.5" />
             <span>Curriculum: {qdrantOk ? 'Connected' : 'Offline'}</span>
           </div>
        )}
        {role === 'faculty' && contextInfo.classLevel && (
          <span className="px-3 py-1 bg-indigo-500/20 text-indigo-200 border border-indigo-500/30 rounded-full text-xs font-bold uppercase tracking-widest shadow-sm">
            {contextInfo.classLevel}
          </span>
        )}
        {role === 'faculty' && contextInfo.language && (
          <span className="px-3 py-1 bg-slate-800 text-slate-300 border border-slate-700 rounded-full text-xs font-medium shadow-sm">
            {contextInfo.language}
          </span>
        )}
        {role === 'learner' && contextInfo.standard && (
          <span className="px-3 py-1 bg-violet-500/20 text-violet-200 border border-violet-500/30 rounded-full text-xs font-bold uppercase tracking-widest shadow-sm">
            {contextInfo.standard}
          </span>
        )}
      </div>
    </div>
  )
}
