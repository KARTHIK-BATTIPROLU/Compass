"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { createClient } from "@/utils/supabase/client";
import { BookOpen, Clock, Tag } from "lucide-react";

interface TopicNode {
  topic_id: string;
  name: string;
  parent_id: string | null;
}

interface Session {
  id: string;
  title: string | null;
  summary: string | null;
  started_at: string;
  topics: TopicNode[];
}

function buildTopicTree(topics: TopicNode[]): { node: TopicNode; children: TopicNode[] }[] {
  const byId = new Map(topics.map(t => [t.topic_id, t]));
  const roots = topics.filter(t => !t.parent_id || !byId.has(t.parent_id));
  return roots.map(root => ({
    node: root,
    children: topics.filter(t => t.parent_id === root.topic_id),
  }));
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function SessionsTopicsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Session | null>(null);

  useEffect(() => {
    const load = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // Fetch sessions via the backend — this is also the summarizer's lazy
      // trigger point: any session with >=4 messages and no summary yet gets
      // one generated here (see agent/memory_summarizer.py).
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const { authedFetch } = await import("@/lib/api");
      let sessData: { id: string; title: string | null; summary: string | null; started_at: string }[] = [];
      try {
        const res = await authedFetch(`${API}/api/memory/sessions/mine`);
        const data = await res.json();
        sessData = data.sessions || [];
      } catch {
        setLoading(false);
        return;
      }

      // For each session, fetch its topics via the memory API
      const enriched: Session[] = await Promise.all(
        sessData.map(async (s) => {
          try {
            const res = await authedFetch(`${API}/api/memory/topics/${s.id}`);
            const data = await res.json();
            return { ...s, topics: data.topics || [] };
          } catch {
            return { ...s, topics: [] };
          }
        })
      );

      setSessions(enriched);
      setLoading(false);
    };
    load();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 md:p-10">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-indigo-900/20 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Sessions &amp; Topics</h1>
          <p className="text-slate-400 mt-1">Every learning session, with the topics you covered.</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="liquid-glass bg-slate-800/40 border border-white/10 rounded-3xl p-12 text-center">
            <span className="text-5xl mb-4 block">🗓️</span>
            <h2 className="text-xl font-semibold text-slate-200 mb-2">No Sessions Yet</h2>
            <p className="text-slate-400 text-sm">Start a chat session to see it here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((sess, i) => (
              <motion.div
                key={sess.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => setSelected(selected?.id === sess.id ? null : sess)}
                className="liquid-glass liquid-glass-sm bg-slate-800/40 border border-white/10 hover:border-white/20 rounded-2xl p-5 cursor-pointer transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
                      <BookOpen className="w-4 h-4 text-indigo-300" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-200 group-hover:text-white transition-colors">
                        {sess.title || "Untitled Session"}
                      </p>
                      <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(sess.started_at)}</span>
                      </div>
                      {sess.summary && (
                        <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 max-w-md">{sess.summary}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 shrink-0">
                    {sess.topics.length} topic{sess.topics.length !== 1 ? "s" : ""}
                  </span>
                </div>

                {/* Topic tree — root topics with drill-down subtopics indented beneath (Part B3) */}
                {sess.topics.length > 0 && (
                  <div className="flex flex-col gap-2 mt-4">
                    {buildTopicTree(sess.topics).map(({ node, children }) => (
                      <div key={node.topic_id} className="flex flex-wrap items-center gap-2">
                        <span className="flex items-center gap-1 px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-xs text-indigo-300">
                          <Tag className="w-2.5 h-2.5" />
                          {node.name}
                        </span>
                        {children.map(child => (
                          <span
                            key={child.topic_id}
                            className="flex items-center gap-1 pl-3 py-1 pr-2.5 ml-1 border-l border-indigo-500/20 text-xs text-indigo-300/80"
                          >
                            <span className="text-indigo-500/40">↳</span>
                            {child.name}
                          </span>
                        ))}
                      </div>
                    ))}
                  </div>
                )}

                {/* Expanded: link to chat */}
                {selected?.id === sess.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="mt-4 pt-4 border-t border-white/10"
                  >
                    <a
                      href={`/learn/chat/${sess.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/30 rounded-xl text-sm text-indigo-200 transition-colors"
                    >
                      Open Session →
                    </a>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
