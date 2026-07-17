"use client";

import { useState, useRef, useEffect } from "react";
import { FloatingChips } from "./FloatingChips";
import { Send, Loader2 } from "lucide-react";
import { ArtifactRenderer } from "./ArtifactRenderer";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatUIProps {
  sessionId: string;
  role: "faculty" | "learner";
  availableChips: string[];
  initialMessages?: Message[];
}

export function ChatUI({ sessionId, role, availableChips, initialMessages = [] }: ChatUIProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [activeChips, setActiveChips] = useState<string[]>(["Detailed"]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleChip = (chip: string) => {
    setActiveChips(prev => 
      prev.includes(chip) ? prev.filter(c => c !== chip) : [...prev, chip]
    );
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          prompt: userMessage.content,
          modes: activeChips
        })
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      let done = false;
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ") && line !== "data: [DONE]") {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.content) {
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.content += data.content;
                    return newMessages;
                  });
                }
              } catch (e) {
                console.error("Error parsing stream data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const userBgClass = role === 'faculty' 
    ? 'bg-indigo-600/20 border-indigo-500/30' 
    : 'bg-violet-600/20 border-violet-500/30';
  const focusBorderClass = role === 'faculty' ? 'focus:border-indigo-500' : 'focus:border-violet-500';
  const btnBgClass = role === 'faculty' ? 'bg-indigo-600' : 'bg-violet-600';

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-8">
      <FloatingChips chips={availableChips} activeChips={activeChips} onToggle={toggleChip} />
      
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-6 pb-4 scroll-smooth"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-60">
             <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-indigo-500/20 to-fuchsia-500/20 animate-pulse flex items-center justify-center border border-white/5 shadow-2xl">
                <span className="text-4xl">👋</span>
             </div>
             <div className="space-y-2">
               <h2 className="text-xl font-bold text-slate-200">Welcome to LearnForge</h2>
               <p className="text-slate-400 text-sm max-w-sm mx-auto">Toggle some chips above and ask a question to generate rich, contextual artifacts.</p>
             </div>
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-3xl p-6 backdrop-blur-xl border ${
              msg.role === 'user' 
                ? `${userBgClass} text-white rounded-br-sm shadow-[0_4px_30px_rgba(0,0,0,0.1)]` 
                : 'bg-slate-800/40 border-white/10 text-slate-200 rounded-bl-sm shadow-xl'
            }`}>
              {msg.role === 'user' ? (
                <div className="whitespace-pre-wrap">{msg.content}</div>
              ) : (
                <ArtifactRenderer content={msg.content} />
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
             <div className="bg-slate-800/40 border border-white/10 p-4 rounded-3xl rounded-bl-sm text-slate-400 shadow-xl">
               <Loader2 className="w-5 h-5 animate-spin" />
             </div>
          </div>
        )}
      </div>

      <div className="pt-4 pb-2">
        <form onSubmit={handleSend} className="relative">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className={`w-full bg-slate-900/60 backdrop-blur-md border border-slate-700 ${focusBorderClass} rounded-2xl py-4 pl-6 pr-14 text-white outline-none shadow-2xl transition-all placeholder:text-slate-500`}
          />
          <button 
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl ${btnBgClass} text-white disabled:opacity-50 transition-opacity hover:opacity-90 shadow-lg`}
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
