import { Sidebar } from "@/components/chat/Sidebar";
import { createClient } from "@/utils/supabase/server";

export default async function FacultyLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  let sessions = [];
  if (user) {
    const { data } = await supabase.from('sessions')
        .select('id, title')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });
    sessions = data || [];
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      <Sidebar sessions={sessions} role="faculty" />
      <div className="flex-1 flex flex-col relative overflow-hidden">
        {children}
      </div>
    </div>
  )
}
