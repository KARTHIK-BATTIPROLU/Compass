import { createClient } from "@/utils/supabase/server";

export default async function PublicQuizPage({ params }: { params: { token: string } }) {
  const supabase = await createClient();
  const { data } = await supabase.from('quizzes').select('*').eq('share_token', params.token).single();
  
  if (!data) return <div className="text-white p-8">Quiz not found</div>;
  
  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center p-4 py-12 relative overflow-hidden">
       <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/30 via-slate-950 to-slate-950" />
       <div className="liquid-glass liquid-glass-lg relative z-10 bg-slate-900/50 border border-slate-800 p-8 rounded-3xl max-w-2xl w-full text-white shadow-2xl">
          <div className="mb-8 border-b border-slate-800 pb-4">
             <h1 className="text-3xl font-bold mb-2 text-indigo-400">{data.questions?.title || "Class Quiz"}</h1>
             <p className="text-slate-400 text-sm">Enter your name to begin taking the quiz. Results will be sent to the instructor.</p>
          </div>

          <div className="space-y-6">
            {data.questions?.questions?.map((q: any, idx: number) => (
              <div key={idx} className="liquid-glass liquid-glass-sm bg-slate-800/50 p-5 rounded-2xl border border-white/5">
                <h3 className="font-semibold text-lg mb-4">{idx + 1}. {q.text}</h3>
                <div className="space-y-2">
                  {q.options?.map((opt: string, i: number) => (
                    <label key={i} className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-600 transition-colors">
                      <input type="radio" name={`q-${idx}`} className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 bg-slate-900 border-slate-700" />
                      <span className="text-slate-300">{opt}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8">
             <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-2xl shadow-lg transition-colors">
               Submit Answers
             </button>
          </div>
       </div>
    </main>
  );
}
