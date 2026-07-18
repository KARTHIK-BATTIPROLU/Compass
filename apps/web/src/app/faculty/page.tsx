import { createFacultySession } from "./actions"

export default function FacultyDashboard() {
  return (
    <main className="min-h-screen flex items-center justify-center platform-mesh platform-mesh-faculty p-4">
      <div className="liquid-glass liquid-glass-lg relative z-10 bg-bg-panel rounded-3xl p-8 border border-steel/20 shadow-2xl max-w-md w-full">
        <h1 className="font-display text-3xl font-semibold text-white mb-2 text-center">Select class</h1>
        <p className="text-steel mb-8 text-center">Which class are you preparing for today?</p>

        <form action={createFacultySession} className="flex flex-col gap-4">
          <button type="submit" name="class_level" value="9th" className="w-full py-4 bg-white/5 hover:bg-ember/15 border border-steel/20 hover:border-ember/50 rounded-xl text-white text-lg font-medium transition-all">
             9th Standard
          </button>
          <button type="submit" name="class_level" value="10th" className="w-full py-4 bg-white/5 hover:bg-ember/15 border border-steel/20 hover:border-ember/50 rounded-xl text-white text-lg font-medium transition-all">
             10th Standard
          </button>
          <button type="submit" name="class_level" value="UG" className="w-full py-4 bg-white/5 hover:bg-ember/15 border border-steel/20 hover:border-ember/50 rounded-xl text-white text-lg font-medium transition-all">
             Undergrad
          </button>
        </form>
      </div>
    </main>
  )
}
