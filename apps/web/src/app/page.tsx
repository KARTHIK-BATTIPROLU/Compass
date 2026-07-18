"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { GraduationCap, BookOpen } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950 text-slate-50">
      {/* Background Gradient Mesh */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="absolute -bottom-[40%] -left-[20%] w-[80%] h-[80%] bg-violet-600/30 blur-[120px] rounded-full mix-blend-screen" />
      <div className="absolute -top-[40%] -right-[20%] w-[80%] h-[80%] bg-indigo-600/30 blur-[120px] rounded-full mix-blend-screen" />
      
      <div className="relative z-10 container mx-auto px-4 py-16 flex flex-col items-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 via-white to-violet-200">
            LearnForge
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto font-light">
            One AI engine. Two tailored experiences. Which platform do you need today?
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Faculty Door */}
          <Link href="/faculty" className="group focus:outline-none">
            <motion.div 
              whileHover={{ scale: 1.02, y: -5 }}
              whileTap={{ scale: 0.98 }}
              className="h-full relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-b from-white/15 to-white/5"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="liquid-glass liquid-glass-lg h-full bg-slate-900/40 rounded-3xl p-8 flex flex-col items-center text-center border border-white/10 shadow-2xl transition-all duration-300 group-hover:border-indigo-400/50 group-hover:shadow-indigo-500/20 group-focus:ring-2 group-focus:ring-indigo-400">
                <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-indigo-500/30">
                  <GraduationCap className="w-8 h-8 text-indigo-300" />
                </div>
                <h2 className="text-3xl font-bold mb-4 text-white">I'm Faculty</h2>
                <p className="text-slate-400 font-light">
                  Generate lecture flows, tiered scripts, and assessments tailored to your curriculum.
                </p>
              </div>
            </motion.div>
          </Link>

          {/* Learner Door */}
          <Link href="/learn" className="group focus:outline-none">
            <motion.div 
              whileHover={{ scale: 1.02, y: -5 }}
              whileTap={{ scale: 0.98 }}
              className="h-full relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-b from-white/15 to-white/5"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="liquid-glass liquid-glass-lg h-full bg-slate-900/40 rounded-3xl p-8 flex flex-col items-center text-center border border-white/10 shadow-2xl transition-all duration-300 group-hover:border-violet-400/50 group-hover:shadow-violet-500/20 group-focus:ring-2 group-focus:ring-violet-400">
                <div className="w-16 h-16 rounded-2xl bg-violet-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-violet-500/30">
                  <BookOpen className="w-8 h-8 text-violet-300" />
                </div>
                <h2 className="text-3xl font-bold mb-4 text-white">I'm a Learner</h2>
                <p className="text-slate-400 font-light">
                  Get step-by-step explanations, diagrams, resources, and track your weak spots automatically.
                </p>
              </div>
            </motion.div>
          </Link>
        </div>
      </div>
    </main>
  );
}
