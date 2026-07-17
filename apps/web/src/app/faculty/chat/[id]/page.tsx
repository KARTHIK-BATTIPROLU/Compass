import { ChatUI } from "@/components/chat/ChatUI";
import { SessionHeader } from "@/components/chat/SessionHeader";
import { createClient } from "@/utils/supabase/server";

export default async function FacultyChatPage({ params }: { params: { id: string } }) {
  const supabase = await createClient();
  
  const { data: messages } = await supabase.from('messages')
    .select('role, content')
    .eq('session_id', params.id)
    .order('created_at', { ascending: true });
    
  const { data: session } = await supabase.from('sessions').select('class_level, user_id').eq('id', params.id).single();
  const { data: userRecord } = await supabase.from('users').select('language').eq('id', session?.user_id).single();

  const facultyChips = ["Detailed", "Curriculum", "Lecture Script", "Socratic"];

  return (
    <main className="h-full bg-slate-950 flex flex-col relative">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/40 via-slate-950 to-slate-950 opacity-80 pointer-events-none" />
      
      <SessionHeader role="faculty" contextInfo={{ classLevel: session?.class_level, language: userRecord?.language }} />
      
      <div className="relative z-10 flex-1 overflow-hidden">
         <ChatUI 
           sessionId={params.id} 
           role="faculty" 
           availableChips={facultyChips} 
           initialMessages={messages || []}
         />
      </div>
    </main>
  )
}
