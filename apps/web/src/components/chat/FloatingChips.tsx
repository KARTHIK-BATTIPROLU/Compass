"use client";

import { motion, useReducedMotion } from "framer-motion";

interface FloatingChipsProps {
  chips: string[];
  activeChips: string[];
  onToggle: (chip: string) => void;
}

const WAS_LABELS = new Set(["w-a-s", "was", "weak-average-strong"]);

export function FloatingChips({ chips, activeChips, onToggle }: FloatingChipsProps) {
  const reduceMotion = useReducedMotion();

  return (
    <div className="flex flex-wrap gap-2.5 justify-center">
      {chips.map(chip => {
        const isActive = activeChips.includes(chip);
        const isWas = WAS_LABELS.has(chip.trim().toLowerCase());
        return (
          <motion.button
            key={chip}
            type="button"
            onClick={() => onToggle(chip)}
            whileHover={reduceMotion ? undefined : { scale: 1.05, y: -2 }}
            whileTap={reduceMotion ? undefined : { scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 22 }}
            aria-pressed={isActive}
            className={`liquid-glass liquid-glass-sm relative overflow-hidden flex items-center gap-2 pl-3.5 pr-4 py-2 rounded-full whitespace-nowrap text-sm font-medium border transition-colors ${
              isActive
                ? "ember-glow bg-ember/15 text-ember-hot border-ember/60"
                : "bg-bg-panel text-steel border-steel/25 hover:text-slate-100 hover:border-steel/40"
            }`}
          >
            {isWas && <span className="was-seam w-[3px] self-stretch -ml-1 rounded-full" aria-hidden="true" />}
            <span className="relative z-10">{chip}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
