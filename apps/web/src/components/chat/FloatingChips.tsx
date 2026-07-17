"use client";

import { motion } from "framer-motion";

interface FloatingChipsProps {
  chips: string[];
  activeChips: string[];
  onToggle: (chip: string) => void;
}

export function FloatingChips({ chips, activeChips, onToggle }: FloatingChipsProps) {
  return (
    <div className="flex flex-wrap gap-3 justify-center mb-6">
      {chips.map(chip => {
        const isActive = activeChips.includes(chip);
        return (
          <motion.button
            key={chip}
            onClick={() => onToggle(chip)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-colors shadow-lg backdrop-blur-md border ${
              isActive 
                ? 'bg-indigo-600/90 text-white border-indigo-400/50 shadow-[0_0_15px_rgba(99,102,241,0.5)]' 
                : 'bg-slate-800/60 text-slate-300 border-white/10 hover:bg-slate-700/80'
            }`}
          >
            <span className="relative z-10">{chip}</span>
          </motion.button>
        )
      })}
    </div>
  )
}
