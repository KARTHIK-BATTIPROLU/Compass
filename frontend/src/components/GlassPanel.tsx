import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function GlassPanel({
  children,
  className,
  as: Tag = 'div',
}: {
  children: ReactNode
  className?: string
  as?: 'div' | 'section' | 'article'
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 320, damping: 28 }}
    >
      <Tag
        className={cn(
          'rounded-2xl border border-[var(--color-glass-border)] bg-[var(--color-glass)]',
          'backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.35)]',
          className,
        )}
      >
        {children}
      </Tag>
    </motion.div>
  )
}

export function SkeletonBlock({ className }: { className?: string }) {
  return <div className={cn('shimmer rounded-lg bg-white/5', className)} />
}
