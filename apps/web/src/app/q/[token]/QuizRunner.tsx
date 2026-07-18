"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

interface Question {
  id: string;
  topic?: string;
  text: string;
  options: string[];
  correctAnswer: number;
  explanation?: string;
}

interface QuizRunnerProps {
  token: string;
  title: string;
  questions: Question[];
  apiBase: string;
}

type Stage = "name" | "question" | "submitting" | "done" | "error";

export function QuizRunner({ token, title, questions, apiBase }: QuizRunnerProps) {
  const reduceMotion = useReducedMotion();
  const [stage, setStage] = useState<Stage>("name");
  const [name, setName] = useState("");
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [errorMsg, setErrorMsg] = useState("");

  const total = questions.length;
  const q = questions[index];
  const progress = stage === "question" ? Math.round(((index) / total) * 100) : 0;

  const selectAnswer = (optionIndex: number) => {
    setAnswers(a => ({ ...a, [q.id]: optionIndex }));
  };

  const goNext = async () => {
    if (index < total - 1) {
      setIndex(i => i + 1);
      return;
    }
    await submit();
  };

  const submit = async () => {
    setStage("submitting");
    setErrorMsg("");

    let correct = 0;
    const perTopic: Record<string, { correct: number; total: number }> = {};
    for (const question of questions) {
      const topic = question.topic || "General";
      perTopic[topic] = perTopic[topic] || { correct: 0, total: 0 };
      perTopic[topic].total += 1;
      if (answers[question.id] === question.correctAnswer) {
        correct += 1;
        perTopic[topic].correct += 1;
      }
    }
    const scorePct = Math.round((correct / total) * 100);
    const perTopicScores: Record<string, number> = {};
    for (const [topic, v] of Object.entries(perTopic)) {
      perTopicScores[topic] = Math.round((v.correct / v.total) * 100);
    }

    try {
      const res = await fetch(`${apiBase}/api/quiz/${token}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quiz_id: token,
          respondent_name: name.trim(),
          answers,
          score: scorePct,
          per_topic: perTopicScores,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Submission failed — please try again.");
      }
      setStage("done");
    } catch (e: any) {
      setErrorMsg(e.message || "Something went wrong submitting your answers.");
      setStage("error");
    }
  };

  return (
    <main className="min-h-screen platform-mesh platform-mesh-learner flex flex-col items-center p-4 py-10 text-white">
      <div className="w-full max-w-md mx-auto">
        {/* Ember progress bar */}
        {stage === "question" && (
          <div className="mb-6">
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-ember"
                initial={false}
                animate={{ width: `${progress}%` }}
                transition={{ duration: reduceMotion ? 0 : 0.3 }}
              />
            </div>
            <p className="text-xs text-steel font-mono mt-2 text-center">Question {index + 1} of {total}</p>
          </div>
        )}

        <AnimatePresence mode="wait">
          {stage === "name" && (
            <motion.div
              key="name"
              initial={reduceMotion ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
              className="liquid-glass liquid-glass-lg bg-bg-panel border border-steel/20 rounded-3xl p-6 shadow-2xl"
            >
              <h1 className="font-display text-2xl font-semibold mb-2">{title}</h1>
              <p className="text-steel text-sm mb-6">Enter your name to begin. Your teacher will see your results.</p>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                maxLength={80}
                className="w-full bg-black/20 border border-steel/25 focus:border-ember rounded-xl px-4 py-4 text-white text-lg outline-none transition-colors placeholder:text-steel/50 mb-4"
              />
              <button
                type="button"
                disabled={!name.trim() || total === 0}
                onClick={() => setStage("question")}
                className="w-full bg-ember hover:bg-ember-hot disabled:bg-white/5 disabled:text-steel/50 text-bg-deep font-semibold text-lg py-4 rounded-2xl transition-colors"
              >
                {total === 0 ? "No questions in this quiz" : "Start quiz"}
              </button>
            </motion.div>
          )}

          {stage === "question" && q && (
            <motion.div
              key={q.id}
              initial={reduceMotion ? false : { opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, x: -24 }}
              transition={{ duration: reduceMotion ? 0 : 0.25 }}
              className="liquid-glass liquid-glass-lg bg-bg-panel border border-steel/20 rounded-3xl p-6 shadow-2xl"
            >
              <h2 className="font-display text-xl font-semibold mb-6 leading-snug">{q.text}</h2>
              <div className="space-y-3 mb-6">
                {q.options?.map((opt, i) => {
                  const selected = answers[q.id] === i;
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => selectAnswer(i)}
                      className={`w-full text-left flex items-center gap-3 p-4 rounded-2xl border text-base transition-colors ${
                        selected
                          ? "bg-ember/15 border-ember text-white"
                          : "bg-black/10 border-steel/20 text-slate-200 hover:border-steel/40"
                      }`}
                    >
                      <span className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center ${selected ? "border-ember" : "border-steel/40"}`}>
                        {selected && <span className="w-2.5 h-2.5 rounded-full bg-ember" />}
                      </span>
                      {opt}
                    </button>
                  );
                })}
              </div>
              <button
                type="button"
                disabled={answers[q.id] === undefined}
                onClick={goNext}
                className="w-full bg-ember hover:bg-ember-hot disabled:bg-white/5 disabled:text-steel/50 text-bg-deep font-semibold text-lg py-4 rounded-2xl transition-colors"
              >
                {index < total - 1 ? "Next question" : "Submit answers"}
              </button>
            </motion.div>
          )}

          {stage === "submitting" && (
            <motion.div key="submitting" className="text-center py-16">
              <div className="w-10 h-10 border-2 border-ember border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-steel">Submitting your answers…</p>
            </motion.div>
          )}

          {stage === "done" && (
            <motion.div
              key="done"
              initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="liquid-glass liquid-glass-lg bg-bg-panel border border-mint/30 rounded-3xl p-8 shadow-2xl text-center"
            >
              <CheckCircle2 className="w-14 h-14 text-mint mx-auto mb-4" />
              <h2 className="font-display text-2xl font-semibold mb-2">All done, {name.split(" ")[0]}!</h2>
              <p className="text-steel text-sm">Your answers were submitted. Your teacher will see your results.</p>
            </motion.div>
          )}

          {stage === "error" && (
            <motion.div
              key="error"
              initial={reduceMotion ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="liquid-glass bg-bg-panel border border-red-500/30 rounded-3xl p-6 shadow-2xl text-center"
            >
              <p className="text-red-200 text-sm mb-4">{errorMsg}</p>
              <button
                type="button"
                onClick={submit}
                className="w-full bg-ember hover:bg-ember-hot text-bg-deep font-semibold py-3 rounded-xl transition-colors"
              >
                Try again
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
