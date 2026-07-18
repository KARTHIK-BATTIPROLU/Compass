"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FloatingChips } from "./FloatingChips";
import { Send, Loader2, AlertCircle } from "lucide-react";
import { ArtifactRenderer } from "./ArtifactRenderer";

interface Artifact {
  id: string;
  type: string;
  content: string;
}

interface Citation {
  id: string | number;
  title: string;
  url: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  artifacts?: Artifact[];
  citations?: Citation[];
  isError?: boolean;
}

interface ChatUIProps {
  sessionId: string;
  role: "faculty" | "learner";
  availableChips: string[];
  initialMessages?: Message[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Add empty assistant message that we'll stream into
    setMessages(prev => [...prev, { role: "assistant", content: "", artifacts: [], citations: [] }]);

    try {
      const { authedFetch } = await import("@/lib/api");
      const response = await authedFetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          prompt: userMessage.content,
          modes: activeChips,
        }),
      });

      if (!response.body) throw new Error("No response body from server");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (!value) continue;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "token" && data.content) {
              // Append streamed token to last message
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  content: msgs[msgs.length - 1].content + data.content,
                };
                return msgs;
              });
            } else if (data.type === "artifacts" && Array.isArray(data.data)) {
              // Attach artifacts to last message
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  artifacts: [...(msgs[msgs.length - 1].artifacts || []), ...data.data],
                };
                return msgs;
              });
            } else if (data.type === "citations" && Array.isArray(data.data)) {
              // Attach citations to last message
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  citations: [...(msgs[msgs.length - 1].citations || []), ...data.data],
                };
                return msgs;
              });
            } else if (data.type === "error") {
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  content: data.content || "An error occurred.",
                  isError: true,
                };
                return msgs;
              });
            }
          } catch {
            // Ignore malformed SSE lines
          }
        }
      }
    } catch (error) {
      console.error("Chat stream error:", error);
      setMessages(prev => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = {
          ...msgs[msgs.length - 1],
          content: "Connection error — please check the API server is running.",
          isError: true,
        };
        return msgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const accentClass = role === "faculty" ? "indigo" : "violet";
  const userBgClass = role === "faculty"
    ? "bg-indigo-600/20 border-indigo-500/30"
    : "bg-violet-600/20 border-violet-500/30";
  const focusBorderClass = role === "faculty" ? "focus:border-indigo-500" : "focus:border-violet-500";
  const btnBgClass = role === "faculty" ? "bg-indigo-600 hover:bg-indigo-700" : "bg-violet-600 hover:bg-violet-700";

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-8">
      <FloatingChips chips={availableChips} activeChips={activeChips} onToggle={toggleChip} />

      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-6 pb-4 scroll-smooth">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-70"
          >
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-indigo-500/20 to-fuchsia-500/20 animate-pulse flex items-center justify-center border border-white/5 shadow-2xl">
              <span className="text-4xl">👋</span>
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-200">Welcome to LearnForge</h2>
              <p className="text-slate-400 text-sm max-w-sm mx-auto">
                Toggle chips above and ask a question to generate rich, contextual artifacts.
              </p>
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`liquid-glass liquid-glass-flat max-w-[85%] rounded-3xl p-6 border shadow-xl ${
                msg.role === "user"
                  ? `${userBgClass} text-white rounded-br-sm`
                  : msg.isError
                  ? "bg-red-900/30 border-red-500/30 text-red-200 rounded-bl-sm"
                  : "bg-slate-800/40 border-white/10 text-slate-200 rounded-bl-sm"
              }`}>
                {msg.role === "user" ? (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <div className="space-y-4">
                    {msg.isError && (
                      <div className="flex items-center gap-2 text-red-300">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span className="text-sm font-medium">Error</span>
                      </div>
                    )}
                    {/* Streaming text content */}
                    {msg.content && <ArtifactRenderer content={msg.content} />}

                    {/* Structured artifacts panel */}
                    {msg.artifacts && msg.artifacts.length > 0 && (
                      <div className="space-y-4 mt-2">
                        {msg.artifacts.map((art: any) => (
                          <ArtifactRenderer key={art.id} content={art.content} artifactType={art.type} downloadUrl={art.download_url} />
                        ))}
                      </div>
                    )}

                    {/* Citations footer */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="border-t border-white/10 pt-3 mt-3">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">Citations</p>
                        <ul className="space-y-1">
                          {msg.citations.map((c, ci) => (
                            <li key={ci} className="flex items-start gap-2 text-xs text-slate-400">
                              <span className="text-slate-500 font-mono shrink-0">[{c.id}]</span>
                              <a href={c.url} target="_blank" rel="noopener noreferrer"
                                className="hover:text-slate-200 underline underline-offset-2 transition-colors break-all">
                                {c.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="liquid-glass liquid-glass-flat bg-slate-800/40 border border-white/10 p-4 rounded-3xl rounded-bl-sm shadow-xl">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
            </div>
          </motion.div>
        )}
      </div>

      {/* Input bar */}
      <div className="pt-4 pb-2">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className={`liquid-glass liquid-glass-sm liquid-glass-flat w-full bg-slate-900/60 border border-slate-700 ${focusBorderClass} rounded-2xl py-4 pl-6 pr-14 text-white outline-none shadow-2xl transition-all placeholder:text-slate-500`}
          />
          <motion.button
            type="submit"
            disabled={!input.trim() || isLoading}
            whileTap={{ scale: 0.95 }}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl ${btnBgClass} text-white disabled:opacity-40 transition-all shadow-lg`}
          >
            <Send className="w-5 h-5" />
          </motion.button>
        </form>
      </div>
    </div>
  );
}
