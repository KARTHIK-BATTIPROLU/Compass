import { completeFacultyOnboarding } from "../actions";

export default function FacultyOnboardingPage() {
  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950 text-slate-50">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="liquid-glass liquid-glass-lg bg-slate-900/40 rounded-3xl p-8 border border-white/10 shadow-2xl">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome, Faculty!</h1>
          <p className="text-slate-400 mb-8 font-light">Tell us a bit about your teaching context so we can tailor the agent to your curriculum.</p>
          
          <form action={completeFacultyOnboarding} className="space-y-6">
            <div>
              <label htmlFor="region" className="block text-sm font-medium text-slate-300 mb-2">Region / Board</label>
              <input 
                type="text" 
                id="region" 
                name="region" 
                placeholder="e.g. CBSE, ICSE, Telangana State Board" 
                required
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label htmlFor="language" className="block text-sm font-medium text-slate-300 mb-2">Primary Teaching Language</label>
              <select 
                id="language" 
                name="language" 
                required
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
              >
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
                <option value="Telugu">Telugu</option>
                <option value="Tamil">Tamil</option>
                <option value="Kannada">Kannada</option>
              </select>
            </div>

            <div>
              <label htmlFor="subjects" className="block text-sm font-medium text-slate-300 mb-2">Subjects (Optional)</label>
              <input 
                type="text" 
                id="subjects" 
                name="subjects" 
                placeholder="e.g. Biology, Physics, Computer Science" 
                className="w-full bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button 
              type="submit"
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-indigo-900/50 mt-4"
            >
              Complete Setup
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
