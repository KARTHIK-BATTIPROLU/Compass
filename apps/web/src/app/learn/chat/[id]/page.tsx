import { ChatUI } from "@/components/chat/ChatUI";
import { SessionHeader } from "@/components/chat/SessionHeader";
import { createClient } from "@/utils/supabase/server";

export default async function LearnerChatPage({ params, searchParams }: { params: { id: string }; searchParams: { prefill?: string } }) {
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
    <main className="h-full flex flex-col relative">
      <SessionHeader role="learner" contextInfo={{ standard: userRecord?.standard }} />

      <div className="relative z-10 flex-1 overflow-hidden">
         <ChatUI
           sessionId={params.id}
           role="learner"
           availableChips={learnerChips}
           initialMessages={messages || []}
           initialInput={searchParams?.prefill || ""}
         />
      </div>
    </main>
  )
}
