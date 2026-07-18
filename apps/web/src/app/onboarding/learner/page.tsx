import { completeLearnerOnboarding } from "../actions";

export default function LearnerOnboardingPage() {
  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950 text-slate-50">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="liquid-glass liquid-glass-lg bg-slate-900/40 rounded-3xl p-8 border border-white/10 shadow-2xl">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome, Learner!</h1>
          <p className="text-slate-400 mb-8 font-light">Let's set up your profile so we can provide the best resources for your level.</p>
          
          <form action={completeLearnerOnboarding} className="space-y-6">
            <div>
              <label htmlFor="standard" className="block text-sm font-medium text-slate-300 mb-2">Standard / Level</label>
              <select 
                id="standard" 
                name="standard" 
                required
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-violet-500 appearance-none"
              >
                <option value="" disabled selected>Select your level</option>
                <option value="Undergrad">Undergrad (B.Tech, B.Sc, etc.)</option>
                <option value="MBBS">MBBS / Medical</option>
                <option value="High School">High School (9th-12th)</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="branch" className="block text-sm font-medium text-slate-300 mb-2">Branch / Field (Optional)</label>
              <input 
                type="text" 
                id="branch" 
                name="branch" 
                placeholder="e.g. Computer Science, Cardiology" 
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            <div>
              <label htmlFor="goal" className="block text-sm font-medium text-slate-300 mb-2">Exam / Goal Context (Optional)</label>
              <input 
                type="text" 
                id="goal" 
                name="goal" 
                placeholder="e.g. NEET PG, Campus Placements" 
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            <button 
              type="submit"
              className="w-full py-3 px-4 bg-violet-600 hover:bg-violet-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-violet-900/50 mt-4"
            >
              Start Learning
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
