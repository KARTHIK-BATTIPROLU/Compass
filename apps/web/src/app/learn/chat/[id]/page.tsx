import { ChatUI } from "@/components/chat/ChatUI";
import { SessionHeader } from "@/components/chat/SessionHeader";
import { createClient } from "@/utils/supabase/server";

export default async function LearnerChatPage({ params }: { params: { id: string } }) {
  const supabase = await createClient();
  
  const { data: messages } = await supabase.from('messages')
    .select('role, content')
    .eq('session_id', params.id)
    .order('created_at', { ascending: true });
    
  const { data: session } = await supabase.from('sessions').select('user_id').eq('id', params.id).single();
  const { data: userRecord } = await supabase.from('users').select('standard').eq('id', session?.user_id).single();

  const learnerChips = [
    "Detailed",
    "Resource",
    "Diagrams",
    "Flashcards",
    "Quiz",
  ];

  return (
    <main className="h-full bg-slate-950 flex flex-col relative">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-900/40 via-slate-950 to-slate-950 opacity-80 pointer-events-none" />
      
      <SessionHeader role="learner" contextInfo={{ standard: userRecord?.standard }} />
      
      <div className="relative z-10 flex-1 overflow-hidden">
         <ChatUI 
           sessionId={params.id} 
           role="learner" 
           availableChips={learnerChips} 
           initialMessages={messages || []}
         />
      </div>
    </main>
  )
}
