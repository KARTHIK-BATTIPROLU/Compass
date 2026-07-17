"use client";

import Link from "next/link";
import { PlusCircle, MessageSquare } from "lucide-react";

interface SidebarProps {
  sessions: { id: string, title: string | null }[];
  role: "faculty" | "learner";
}

export function Sidebar({ sessions, role }: SidebarProps) {
  const btnBg = role === 'faculty' 
    ? 'hover:bg-indigo-600/20 hover:border-indigo-500/30' 
    : 'hover:bg-violet-600/20 hover:border-violet-500/30';

  return (
    <div className="w-64 h-screen bg-slate-900/80 backdrop-blur-2xl border-r border-white/5 p-4 flex flex-col z-20">
      <Link 
        href={`/${role}`} 
        className={`flex items-center gap-3 w-full py-3 px-4 mb-6 rounded-xl bg-slate-800/50 border border-white/5 text-white font-medium transition-all shadow-lg ${btnBg}`}
      >
        <PlusCircle className="w-5 h-5 text-slate-300" />
        <span>New Session</span>
      </Link>
      
      <div className="flex-1 overflow-y-auto space-y-1 pr-2">
        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 px-2">Recent Chats</div>
        {sessions.map(s => (
          <Link 
            key={s.id} 
            href={`/${role}/chat/${s.id}`}
            className="flex items-center gap-3 px-3 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors group"
          >
            <MessageSquare className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
            <span className="truncate text-sm font-medium">{s.title || "Untitled Session"}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
