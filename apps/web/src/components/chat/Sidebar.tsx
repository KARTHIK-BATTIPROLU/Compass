"use client";

import Link from "next/link";
import { PlusCircle, MessageSquare } from "lucide-react";

interface SidebarProps {
  sessions: { id: string, title: string | null, summary?: string | null }[];
  role: "faculty" | "learner";
}

export function Sidebar({ sessions, role }: SidebarProps) {
  const accent = role === "faculty" ? "ember" : "mint";
  const btnBg = role === "faculty"
    ? "hover:bg-ember/15 hover:border-ember/30"
    : "hover:bg-mint/15 hover:border-mint/30";

  return (
    <div className="liquid-glass liquid-glass-lg w-64 h-screen bg-bg-panel border-r border-steel/10 p-4 flex flex-col z-20">
      <Link
        href={`/${role}`}
        className={`liquid-glass liquid-glass-sm flex items-center gap-3 w-full py-3 px-4 mb-2 rounded-xl bg-white/5 border border-steel/10 text-white font-medium transition-all shadow-lg ${btnBg}`}
      >
        <PlusCircle className={`w-5 h-5 text-${accent}`} />
        <span>New Session</span>
      </Link>

      {role === "faculty" && (
        <Link
          href="/faculty/curriculum"
          className="flex items-center gap-3 w-full py-3 px-4 mb-6 rounded-xl bg-white/[0.02] border border-transparent hover:bg-white/5 hover:border-steel/10 text-steel hover:text-white font-medium transition-all"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
          <span>Curriculum Library</span>
        </Link>
      )}

      {role === "learner" && (
        <>
          <Link
            href="/learn/progress"
            className="flex items-center gap-3 w-full py-3 px-4 mb-1 rounded-xl bg-white/[0.02] border border-transparent hover:bg-white/5 hover:border-steel/10 text-steel hover:text-white font-medium transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
            <span>My Progress</span>
          </Link>
          <Link
            href="/learn/topics"
            className="flex items-center gap-3 w-full py-3 px-4 mb-6 rounded-xl bg-white/[0.02] border border-transparent hover:bg-white/5 hover:border-steel/10 text-steel hover:text-white font-medium transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
            <span>Sessions & Topics</span>
          </Link>
        </>
      )}

      <div className="flex-1 overflow-y-auto space-y-1 pr-2">
        <div className="text-[10px] font-bold text-steel/70 uppercase tracking-widest mb-3 px-2 font-mono">Recent Chats</div>
        {sessions.length === 0 ? (
          <p className="text-xs text-steel/70 px-2 leading-relaxed">
            No sessions yet — start one and it&apos;ll appear here.
          </p>
        ) : (
          sessions.map(s => (
            <Link
              key={s.id}
              href={`/${role}/chat/${s.id}`}
              className="flex items-start gap-3 px-3 py-3 rounded-xl text-steel hover:text-white hover:bg-white/5 transition-colors group"
            >
              <MessageSquare className="w-4 h-4 mt-0.5 opacity-50 group-hover:opacity-100 transition-opacity shrink-0" />
              <div className="min-w-0">
                <span className="block truncate text-sm font-medium">{s.title || "Untitled Session"}</span>
                {s.summary && (
                  <span className="block truncate text-xs text-steel/70 mt-0.5">{s.summary}</span>
                )}
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
