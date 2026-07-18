import { createLearnerSession } from "./actions"

export default function LearnerDashboard() {
  return (
    <main className="min-h-screen flex items-center justify-center platform-mesh platform-mesh-learner p-4">
      <div className="liquid-glass liquid-glass-lg relative z-10 bg-bg-panel rounded-3xl p-8 border border-steel/20 shadow-2xl max-w-md w-full text-center">
        <h1 className="font-display text-3xl font-semibold text-white mb-2">Ready to learn?</h1>
        <p className="text-steel mb-8">Start a new personalized study session.</p>

        <form action={createLearnerSession}>
          <button type="submit" className="w-full py-4 bg-mint hover:bg-emerald-300 rounded-xl text-bg-deep text-lg font-semibold transition-all shadow-lg">
             Start new session
          </button>
        </form>
      </div>
    </main>
  )
}
