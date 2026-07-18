import { createClient } from "@/utils/supabase/server";
import { QuizRunner } from "./QuizRunner";

export default async function PublicQuizPage({ params }: { params: { token: string } }) {
  const supabase = await createClient();
  const { data } = await supabase.from('quizzes').select('*').eq('share_token', params.token).single();

  if (!data) {
    return (
      <main className="min-h-screen platform-mesh platform-mesh-learner flex items-center justify-center p-4 text-white">
        <div className="liquid-glass bg-bg-panel border border-steel/20 rounded-3xl p-8 max-w-sm w-full text-center">
          <span className="text-4xl mb-4 block">🔍</span>
          <h1 className="font-display text-xl font-semibold mb-2">Quiz not found</h1>
          <p className="text-steel text-sm">This link may have expired, or the address might be mistyped. Ask your teacher for a fresh link.</p>
        </div>
      </main>
    );
  }

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <QuizRunner
      token={params.token}
      title={data.questions?.title || "Class Quiz"}
      questions={data.questions?.questions || []}
      apiBase={apiBase}
    />
  );
}
