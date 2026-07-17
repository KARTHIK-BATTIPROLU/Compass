import { AnimatePresence, motion } from 'framer-motion'
import { BookOpen, FileQuestion, GitBranch, NotebookPen } from 'lucide-react'
import { cn } from '@/lib/utils'

const INTENT_BUTTONS: Record<
  string,
  { label: string; contentKey: string; icon: typeof BookOpen }
> = {
  generate_quiz: { label: 'Quiz', contentKey: 'quiz', icon: FileQuestion },
  generate_slides: { label: 'Slides', contentKey: 'slides', icon: BookOpen },
  generate_diagram: { label: 'Diagram', contentKey: 'diagram', icon: GitBranch },
  generate_notes: { label: 'Notes', contentKey: 'notes', icon: NotebookPen },
  answer_directly: { label: 'Notes', contentKey: 'notes', icon: NotebookPen },
}

export function FloatingActionBar({
  intents,
  active,
  onSelect,
}: {
  intents: string[]
  active?: string | null
  onSelect: (contentKey: string) => void
}) {
  const seen = new Set<string>()
  const buttons = intents
    .map((intent) => INTENT_BUTTONS[intent])
    .filter((b): b is NonNullable<typeof b> => {
      if (!b || seen.has(b.contentKey)) return false
      seen.add(b.contentKey)
      return true
    })

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-40 flex justify-center px-3">
      <div className="pointer-events-auto flex max-w-[min(100%,420px)] flex-wrap justify-center gap-2 sm:max-w-none sm:flex-nowrap">
        <AnimatePresence mode="popLayout">
          {buttons.map((btn) => {
            const Icon = btn.icon
            const isActive = active === btn.contentKey
            return (
              <motion.button
                key={btn.contentKey}
                layout
                initial={{ opacity: 0, y: 24, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 16, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 380, damping: 22 }}
                onClick={() => onSelect(btn.contentKey)}
                className={cn(
                  'flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm backdrop-blur-xl',
                  'border-[var(--color-glass-border)] bg-[var(--color-glass)] shadow-lg',
                  isActive && 'border-sky-400/50 bg-sky-500/15 text-sky-100',
                )}
              >
                <Icon size={16} />
                {btn.label}
              </motion.button>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
