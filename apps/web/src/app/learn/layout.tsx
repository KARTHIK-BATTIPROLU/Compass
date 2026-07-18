import { Sidebar } from "@/components/chat/Sidebar";
import { createClient } from "@/utils/supabase/server";

export default async function LearnerLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  let sessions: { id: string; title: string | null; summary: string | null }[] = [];
  if (user) {
    const { data } = await supabase.from('sessions')
        .select('id, title, summary')
        .eq('user_id', user.id)
        .order('started_at', { ascending: false });
    sessions = data || [];
  }

  return (
    <div className="flex h-screen overflow-hidden platform-mesh platform-mesh-learner">
      <Sidebar sessions={sessions} role="learner" />
      <div className="flex-1 flex flex-col relative overflow-hidden">
        {children}
      </div>
    </div>
  )
}
