"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { createClient } from "@/utils/supabase/client";

interface WeaknessTopic {
  topic: string;
  mastery: number;
  last_seen: string;
}

interface MasteryRingProps {
  topic: string;
  mastery: number;
}

function MasteryRing({ topic, mastery }: MasteryRingProps) {
  const pct = Math.round(mastery * 100);
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const dash = (pct / 100) * circ;
  const color = pct < 40 ? "#ef4444" : pct < 70 ? "#f59e0b" : "#22c55e";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center gap-2 p-4 bg-slate-800/40 border border-white/10 rounded-2xl backdrop-blur-md"
    >
      <svg width="72" height="72" className="-rotate-90">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="6" />
        <motion.circle
          cx="36" cy="36" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
        />
      </svg>
      <span className="text-xs font-mono font-bold" style={{ color }}>{pct}%</span>
      <span className="text-xs text-slate-300 text-center leading-tight max-w-[80px] truncate">{topic}</span>
    </motion.div>
  );
}

export default function MyProgressPage() {
  const [weakness, setWeakness] = useState<WeaknessTopic[]>([]);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      setUserId(user.id);

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/memory/weakness?user_id=${user.id}`
        );
        const data = await res.json();
        setWeakness(data.weakness || []);
      } catch (e) {
        console.error("Failed to load weakness profile:", e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const weak = weakness.filter(w => w.mastery < 0.5);
  const good = weakness.filter(w => w.mastery >= 0.5);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 md:p-10">
      {/* Gradient bg */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-violet-900/20 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto space-y-10">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-100">My Progress</h1>
          <p className="text-slate-400 mt-1">Track your mastery across topics you&apos;ve studied.</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 rounded-full border-2 border-violet-400 border-t-transparent animate-spin" />
          </div>
        ) : weakness.length === 0 ? (
          <div className="bg-slate-800/40 border border-white/10 rounded-3xl p-12 text-center">
            <span className="text-5xl mb-4 block">📚</span>
            <h2 className="text-xl font-semibold text-slate-200 mb-2">No Progress Data Yet</h2>
            <p className="text-slate-400 text-sm">
              Start chatting and taking quizzes — your topic mastery will appear here.
            </p>
          </div>
        ) : (
          <>
            {/* Weak topics */}
            {weak.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-red-400 text-lg">⚠️</span>
                  <h2 className="text-lg font-semibold text-slate-200">Topics to Revisit</h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {weak.map((w, i) => (
                    <MasteryRing key={i} topic={w.topic} mastery={w.mastery} />
                  ))}
                </div>
                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl">
                  <p className="text-sm text-red-300">
                    💡 <strong>Tip:</strong> Ask about{" "}
                    <span className="font-semibold">{weak[0]?.topic}</span> in your next chat session to strengthen your understanding.
                  </p>
                </div>
              </section>
            )}

            {/* Good topics */}
            {good.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-green-400 text-lg">✅</span>
                  <h2 className="text-lg font-semibold text-slate-200">Topics You&apos;ve Mastered</h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {good.map((w, i) => (
                    <MasteryRing key={i} topic={w.topic} mastery={w.mastery} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
