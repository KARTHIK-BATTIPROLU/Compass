"use client";

import { memo, useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { FloatingChips } from "./FloatingChips";
import { Send, Loader2, AlertCircle, ArrowUpRight } from "lucide-react";
import { ArtifactRenderer, ArtifactTypeMeta } from "./ArtifactRenderer";
import type { PanelArtifact } from "./ArtifactPanel";

// The slide-in panel (with the flashcard/slide/script sub-renderers) is only
// needed once a user actually opens an artifact — lazy-load it out of the
// initial chat bundle instead of paying for it on every page load.
const ArtifactPanel = dynamic(() => import("./ArtifactPanel").then(m => m.ArtifactPanel), { ssr: false });

interface Artifact {
  id: string;
  type: string;
  content: string;
  download_url?: string;
}

interface Citation {
  id: string | number;
  title: string;
  url: string;
}

interface QuizNudge {
  message: string;
  topics_touched: string[];
}

interface Message {
  role: "user" | "assistant";
  content: string;
  artifacts?: Artifact[];
  citations?: Citation[];
  isError?: boolean;
  nudge?: QuizNudge;
}

interface ChatUIProps {
  sessionId: string;
  role: "faculty" | "learner";
  availableChips: string[];
  initialMessages?: Message[];
  initialInput?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatUI({ sessionId, role, availableChips, initialMessages = [], initialInput = "" }: ChatUIProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState(initialInput);
  const [activeChips, setActiveChips] = useState<string[]>(["Detailed"]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedArtifact, setSelectedArtifact] = useState<PanelArtifact | null>(null);
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
    const prompt = input.trim();
    setInput("");
    await sendMessage(prompt, activeChips);
  };

  const handleNudgeClick = async (topics: string[]) => {
    if (isLoading) return;
    const prompt = topics.length > 0
      ? `Quiz me on: ${topics.join(", ")}`
      : "Quiz me on what we covered in this session";
    await sendMessage(prompt, ["Quiz"]);
  };

  const sendMessage = async (prompt: string, modes: string[]) => {
    if (isLoading) return;

    const userMessage: Message = { role: "user", content: prompt };
    setMessages(prev => [...prev, userMessage]);
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
          modes,
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
            } else if (data.type === "nudge" && data.data) {
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  nudge: data.data,
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

  const userBgClass = role === "faculty"
    ? "bg-ember/15 border-ember/30"
    : "bg-mint/15 border-mint/30";
  const focusBorderClass = role === "faculty" ? "focus:border-ember" : "focus:border-mint";
  const btnBgClass = role === "faculty" ? "bg-ember hover:bg-ember-hot text-bg-deep" : "bg-mint hover:bg-emerald-300 text-bg-deep";

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-8">
      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-6 pb-4 scroll-smooth">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-70"
          >
            <div className={`w-24 h-24 rounded-full bg-gradient-to-tr ${role === "faculty" ? "from-ember/20 to-ember-deep/20" : "from-mint/20 to-teal-500/20"} animate-pulse flex items-center justify-center border border-steel/10 shadow-2xl`}>
              <span className="text-4xl">👋</span>
            </div>
            <div className="space-y-2">
              <h2 className="font-display text-xl font-semibold text-slate-200">Welcome to LearnForge</h2>
              <p className="text-steel text-sm max-w-sm mx-auto">
                No sessions yet — toggle a chip below and ask a question to forge your first artifact.
              </p>
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              msg={msg}
              userBgClass={userBgClass}
              isLoading={isLoading}
              onNudgeClick={handleNudgeClick}
              onOpenArtifact={setSelectedArtifact}
            />
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="liquid-glass liquid-glass-flat bg-bg-panel border border-steel/20 p-4 rounded-3xl rounded-bl-sm shadow-xl">
              <Loader2 className="w-5 h-5 animate-spin text-steel" />
            </div>
          </motion.div>
        )}
      </div>

      {/* Chips float bottom-center, just above the input */}
      <div className="pb-3">
        <FloatingChips chips={availableChips} activeChips={activeChips} onToggle={toggleChip} />
      </div>

      {/* Input bar */}
      <div className="pb-2">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className={`liquid-glass liquid-glass-sm liquid-glass-flat w-full bg-bg-panel border border-steel/25 ${focusBorderClass} rounded-2xl py-4 pl-6 pr-14 text-white outline-none shadow-2xl transition-all placeholder:text-steel/70`}
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

      <ArtifactPanel artifact={selectedArtifact} onClose={() => setSelectedArtifact(null)} />
    </div>
  );
}

// Memoized so a token/artifact/citation update to the currently-streaming
// message doesn't re-render every earlier message in a long session — only
// the message whose object reference actually changed re-renders.
const MessageBubble = memo(function MessageBubble({
  msg,
  userBgClass,
  isLoading,
  onNudgeClick,
  onOpenArtifact,
}: {
  msg: Message;
  userBgClass: string;
  isLoading: boolean;
  onNudgeClick: (topics: string[]) => void;
  onOpenArtifact: (artifact: Artifact & { download_url?: string }) => void;
}) {
  return (
    <motion.div
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
          : "bg-bg-panel border-steel/20 text-slate-200 rounded-bl-sm"
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

            {/* Structured artifacts — quiz share-links render inline (small,
                actionable); everything else is a compact card that opens the
                slide-in artifact panel. */}
            {msg.artifacts && msg.artifacts.length > 0 && (
              <div className="space-y-3 mt-2">
                {msg.artifacts.map((art) =>
                  art.type === "quiz" ? (
                    <ArtifactRenderer key={art.id} content={art.content} artifactType={art.type} downloadUrl={art.download_url} />
                  ) : (
                    <ArtifactCard key={art.id} artifact={art} onOpen={() => onOpenArtifact(art)} />
                  )
                )}
              </div>
            )}

            {/* End-of-session quiz nudge (Part B2) — never auto-fires; only on click */}
            {msg.nudge && (
              <motion.button
                type="button"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => onNudgeClick(msg.nudge!.topics_touched)}
                disabled={isLoading}
                className="flex items-center justify-between w-full gap-3 px-4 py-3 rounded-2xl bg-mint/10 border border-mint/30 hover:bg-mint/20 hover:border-mint/50 text-emerald-200 text-sm font-medium transition-all disabled:opacity-50"
              >
                <span>{msg.nudge.message}</span>
                <span aria-hidden="true">→</span>
              </motion.button>
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
  );
});

function ArtifactCard({ artifact, onOpen }: { artifact: Artifact & { download_url?: string }; onOpen: () => void }) {
  const meta = ArtifactTypeMeta(artifact.type);
  return (
    <motion.button
      type="button"
      onClick={onOpen}
      whileHover={{ y: -1 }}
      className="liquid-glass liquid-glass-sm w-full flex items-center gap-3 text-left bg-bg-panel border border-steel/20 hover:border-steel/40 rounded-2xl p-4 transition-colors"
    >
      <div className="was-seam w-[3px] self-stretch rounded-full shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <span className="font-mono text-[10px] tracking-widest uppercase" style={{ color: meta.color }}>{meta.label}</span>
        <p className="font-display text-sm font-semibold text-white truncate">{meta.title}</p>
      </div>
      <ArrowUpRight className="w-4 h-4 text-steel shrink-0" />
    </motion.button>
  );
}
