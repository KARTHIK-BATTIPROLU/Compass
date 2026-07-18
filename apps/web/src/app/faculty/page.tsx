import { createFacultySession } from "./actions"

export default function FacultyDashboard() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="liquid-glass liquid-glass-lg relative z-10 bg-slate-900/40 rounded-3xl p-8 border border-white/10 shadow-2xl max-w-md w-full">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">Select Class</h1>
        <p className="text-slate-400 mb-8 text-center">Which class are you preparing for today?</p>
        
        <form action={createFacultySession} className="flex flex-col gap-4">
          <button type="submit" name="class_level" value="9th" className="w-full py-4 bg-slate-800/50 hover:bg-indigo-600 border border-slate-700 hover:border-indigo-500 rounded-xl text-white text-lg font-medium transition-all">
             9th Standard
          </button>
          <button type="submit" name="class_level" value="10th" className="w-full py-4 bg-slate-800/50 hover:bg-indigo-600 border border-slate-700 hover:border-indigo-500 rounded-xl text-white text-lg font-medium transition-all">
             10th Standard
          </button>
          <button type="submit" name="class_level" value="UG" className="w-full py-4 bg-slate-800/50 hover:bg-indigo-600 border border-slate-700 hover:border-indigo-500 rounded-xl text-white text-lg font-medium transition-all">
             Undergrad
          </button>
        </form>
      </div>
    </main>
  )
}
