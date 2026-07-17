import { createLearnerSession } from "./actions"

export default function LearnerDashboard() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="relative z-10 bg-slate-900/40 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl max-w-md w-full text-center">
        <h1 className="text-3xl font-bold text-white mb-2">Ready to learn?</h1>
        <p className="text-slate-400 mb-8">Start a new personalized study session.</p>
        
        <form action={createLearnerSession}>
          <button type="submit" className="w-full py-4 bg-violet-600 hover:bg-violet-700 rounded-xl text-white text-lg font-medium transition-all shadow-lg shadow-violet-900/50">
             Start New Session
          </button>
        </form>
      </div>
    </main>
  )
}
