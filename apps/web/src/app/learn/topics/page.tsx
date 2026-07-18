"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
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
  const reduceMotion = useReducedMotion();

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
    <div className="min-h-screen platform-mesh platform-mesh-learner text-white pt-20 px-6 pb-6 md:p-10">
      <div className="relative z-10 max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="font-display text-3xl font-semibold text-slate-100">Sessions &amp; Topics</h1>
          <p className="text-steel mt-1">Every learning session, with the topics you covered.</p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton-shimmer h-24 rounded-2xl border border-steel/15" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="liquid-glass bg-bg-panel border border-steel/20 rounded-3xl p-12 text-center">
            <span className="text-5xl mb-4 block">🗓️</span>
            <h2 className="font-display text-xl font-semibold text-slate-200 mb-2">No sessions yet</h2>
            <p className="text-steel text-sm">Start a chat session and it&apos;ll appear here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((sess, i) => (
              <motion.div
                key={sess.id}
                initial={reduceMotion ? false : { opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: reduceMotion ? 0 : i * 0.04 }}
                onClick={() => setSelected(selected?.id === sess.id ? null : sess)}
                className="liquid-glass liquid-glass-sm bg-bg-panel border border-steel/20 hover:border-steel/35 rounded-2xl p-5 cursor-pointer transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-mint/15 border border-mint/25 flex items-center justify-center shrink-0">
                      <BookOpen className="w-4 h-4 text-mint" />
                    </div>
                    <div>
                      <p className="font-display font-semibold text-slate-200 group-hover:text-white transition-colors">
                        {sess.title || "Untitled Session"}
                      </p>
                      <div className="flex items-center gap-1 text-xs text-steel mt-0.5">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(sess.started_at)}</span>
                      </div>
                      {sess.summary && (
                        <p className="text-xs text-steel/80 mt-1.5 line-clamp-2 max-w-md">{sess.summary}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-steel shrink-0 font-mono">
                    {sess.topics.length} topic{sess.topics.length !== 1 ? "s" : ""}
                  </span>
                </div>

                {/* Topic tree — root topics with drill-down subtopics indented beneath (Part B3) */}
                {sess.topics.length > 0 && (
                  <div className="flex flex-col gap-2 mt-4">
                    {buildTopicTree(sess.topics).map(({ node, children }) => (
                      <div key={node.topic_id} className="flex flex-wrap items-center gap-2">
                        <span className="flex items-center gap-1 px-2.5 py-1 bg-ember/10 border border-ember/25 rounded-full text-xs text-ember">
                          <Tag className="w-2.5 h-2.5" />
                          {node.name}
                        </span>
                        {children.map(child => (
                          <span
                            key={child.topic_id}
                            className="flex items-center gap-1 pl-3 py-1 pr-2.5 ml-1 border-l border-steel/25 text-xs text-steel"
                          >
                            <span className="text-steel/50">↳</span>
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
                    initial={reduceMotion ? false : { opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    transition={{ duration: reduceMotion ? 0 : 0.25 }}
                    className="mt-4 pt-4 border-t border-steel/15"
                  >
                    <a
                      href={`/learn/chat/${sess.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-mint/10 hover:bg-mint/20 border border-mint/30 hover:border-mint/50 rounded-xl text-sm text-mint transition-colors"
                    >
                      Open session →
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
