"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { createClient } from "@/utils/supabase/client";
import { createLearnerSession } from "../actions";

interface WeaknessTopic {
  topic: string;
  mastery: number;
  last_seen: string;
}

function MasteryRing({ topic, mastery, gradientId }: { topic: string; mastery: number; gradientId: string }) {
  const reduceMotion = useReducedMotion();
  const pct = Math.round(mastery * 100);
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const dash = (pct / 100) * circ;

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="liquid-glass liquid-glass-sm flex flex-col items-center gap-2 p-4 bg-bg-panel border border-steel/20 rounded-2xl"
    >
      <svg width="72" height="72" className="-rotate-90">
        <defs>
          {/* The seam, applied along the ring's bounding box — mastery
              growing "fills" more of the weak->strong gradient. */}
          <linearGradient id={gradientId} x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--mint-signal)" />
            <stop offset="55%" stopColor="var(--ember)" />
            <stop offset="100%" stopColor="var(--ember-deep)" />
          </linearGradient>
        </defs>
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <motion.circle
          cx="36" cy="36" r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={reduceMotion ? { strokeDashoffset: circ - dash } : { strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={reduceMotion ? { duration: 0 } : { duration: 1.2, ease: "easeOut", delay: 0.2 }}
        />
      </svg>
      <span className="text-xs font-mono font-bold text-slate-200">{pct}%</span>
      <span className="text-xs text-steel text-center leading-tight max-w-[80px] truncate">{topic}</span>
    </motion.div>
  );
}

function RevisitPill({ topic }: { topic: string }) {
  return (
    <form action={createLearnerSession}>
      <input type="hidden" name="prefill" value={`revisit ${topic}`} />
      <button
        type="submit"
        className="px-3 py-1.5 rounded-full text-xs font-medium border border-ember/40 text-ember hover:bg-ember/10 hover:border-ember/60 transition-colors"
      >
        Revisit {topic} →
      </button>
    </form>
  );
}

export default function MyProgressPage() {
  const [weakness, setWeakness] = useState<WeaknessTopic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      try {
        const { authedFetch } = await import("@/lib/api");
        const res = await authedFetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/memory/weakness`
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
    <div className="min-h-screen platform-mesh platform-mesh-learner text-white p-6 md:p-10">
      <div className="relative z-10 max-w-4xl mx-auto space-y-10">
        <div>
          <h1 className="font-display text-3xl font-semibold text-slate-100">My Progress</h1>
          <p className="text-steel mt-1">Track your mastery across topics you&apos;ve studied.</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton-shimmer h-32 rounded-2xl border border-steel/15" />
            ))}
          </div>
        ) : weakness.length === 0 ? (
          <div className="liquid-glass bg-bg-panel border border-steel/20 rounded-3xl p-12 text-center">
            <span className="text-5xl mb-4 block">📚</span>
            <h2 className="font-display text-xl font-semibold text-slate-200 mb-2">No progress data yet</h2>
            <p className="text-steel text-sm">
              Start chatting and taking quizzes — your topic mastery will appear here.
            </p>
          </div>
        ) : (
          <>
            {weak.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="was-seam w-[3px] h-5 rounded-full" aria-hidden="true" />
                  <h2 className="font-display text-lg font-semibold text-slate-200">Topics to revisit</h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-4">
                  {weak.map((w, i) => (
                    <MasteryRing key={i} topic={w.topic} mastery={w.mastery} gradientId={`ring-weak-${i}`} />
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {weak.map((w, i) => <RevisitPill key={i} topic={w.topic} />)}
                </div>
              </section>
            )}

            {good.length > 0 && (
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-mint text-lg">✓</span>
                  <h2 className="font-display text-lg font-semibold text-slate-200">Topics you&apos;ve mastered</h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {good.map((w, i) => (
                    <MasteryRing key={i} topic={w.topic} mastery={w.mastery} gradientId={`ring-good-${i}`} />
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
