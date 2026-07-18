"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { GraduationCap, BookOpen } from "lucide-react";

const SNIPPETS = [
  {
    tier: "WEAK",
    label: "Foundational",
    color: "var(--mint-signal)",
    text: "Photosynthesis is how plants turn sunlight into food. Let's define every term first.",
  },
  {
    tier: "AVERAGE",
    label: "Standard",
    color: "var(--ember)",
    text: "The Calvin cycle uses ATP and NADPH from the light reactions to fix CO₂ into glucose.",
  },
  {
    tier: "STRONG",
    label: "Advanced",
    color: "var(--ember-deep)",
    text: "Consider RuBisCO's oxygenase activity — why does photorespiration cost the plant carbon?",
  },
];

function CyclingArtifactCard() {
  const [index, setIndex] = useState(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const id = setInterval(() => setIndex((i) => (i + 1) % SNIPPETS.length), 3200);
    return () => clearInterval(id);
  }, []);

  const snippet = SNIPPETS[index];

  return (
    <div className="liquid-glass liquid-glass-sm w-full max-w-md rounded-2xl border border-steel/25 bg-bg-panel shadow-2xl overflow-hidden">
      <div className="flex">
        <div className="was-seam w-[3px] shrink-0" aria-hidden="true" />
        <div className="p-5 flex-1 min-w-0">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-[11px] tracking-widest text-steel uppercase">
              Teaching Script
            </span>
            <span
              className="font-mono text-[11px] tracking-widest uppercase px-2 py-0.5 rounded-full border"
              style={{ color: snippet.color, borderColor: `color-mix(in srgb, ${snippet.color} 40%, transparent)` }}
            >
              {snippet.tier}
            </span>
          </div>
          <AnimatePresence mode="wait">
            <motion.p
              key={snippet.tier}
              initial={reduceMotion ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -6 }}
              transition={{ duration: reduceMotion ? 0 : 0.35 }}
              className="text-sm text-slate-200 leading-relaxed min-h-[3.5rem]"
            >
              {snippet.text}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden platform-mesh px-4 py-16">
      <div className="relative z-10 container mx-auto flex flex-col items-center">
        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.7 }}
          className="text-center mb-10 max-w-2xl"
        >
          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-semibold tracking-tight mb-5 text-slate-50">
            Forge every lesson three ways.
          </h1>
          <p className="text-base sm:text-lg text-steel max-w-xl mx-auto leading-relaxed">
            One prompt goes in. A layered lesson — weak, average, strong — comes out. Same core, three depths, built for the class in front of you.
          </p>
        </motion.div>

        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.7, delay: reduceMotion ? 0 : 0.15 }}
          className="mb-14"
        >
          <CyclingArtifactCard />
        </motion.div>

        <div className="grid sm:grid-cols-2 gap-6 w-full max-w-3xl">
          {/* Faculty Door — warm */}
          <Link href="/faculty" className="group focus:outline-none rounded-3xl">
            <motion.div
              whileHover={reduceMotion ? undefined : { scale: 1.02, y: -5 }}
              whileTap={reduceMotion ? undefined : { scale: 0.98 }}
              transition={{ type: "spring", stiffness: 300, damping: 24 }}
              className="h-full relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-b from-white/15 to-white/5"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-ember/10 to-ember-deep/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="liquid-glass liquid-glass-lg h-full bg-bg-panel rounded-3xl p-8 flex flex-col items-center text-center border border-steel/25 shadow-2xl transition-all duration-300 group-hover:border-ember/50 group-focus-visible:ring-2 group-focus-visible:ring-ember">
                <div className="w-16 h-16 rounded-2xl bg-ember/15 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-ember/25">
                  <GraduationCap className="w-8 h-8 text-ember" />
                </div>
                <h2 className="font-display text-2xl font-semibold mb-3 text-white">I&apos;m Faculty</h2>
                <p className="text-steel text-sm leading-relaxed">
                  Plan, layer, and share your class.
                </p>
              </div>
            </motion.div>
          </Link>

          {/* Learner Door — cool */}
          <Link href="/learn" className="group focus:outline-none rounded-3xl">
            <motion.div
              whileHover={reduceMotion ? undefined : { scale: 1.02, y: -5 }}
              whileTap={reduceMotion ? undefined : { scale: 0.98 }}
              transition={{ type: "spring", stiffness: 300, damping: 24 }}
              className="h-full relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-b from-white/15 to-white/5"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-mint/10 to-teal-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="liquid-glass liquid-glass-lg h-full bg-bg-panel rounded-3xl p-8 flex flex-col items-center text-center border border-steel/25 shadow-2xl transition-all duration-300 group-hover:border-mint/50 group-focus-visible:ring-2 group-focus-visible:ring-mint">
                <div className="w-16 h-16 rounded-2xl bg-mint/15 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-mint/25">
                  <BookOpen className="w-8 h-8 text-mint" />
                </div>
                <h2 className="font-display text-2xl font-semibold mb-3 text-white">I&apos;m a Learner</h2>
                <p className="text-steel text-sm leading-relaxed">
                  Learn it, test it, keep it.
                </p>
              </div>
            </motion.div>
          </Link>
        </div>
      </div>
    </main>
  );
}
