import { FormEvent, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Where did most of my money go this month?",
  "How much did I spend on food?",
  "Can I save ৳5,000 this month?",
  "What's my financial health score?",
];

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get("/ai/status").then((res) => setAiEnabled(res.data.ai_enabled));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || sending) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    try {
      const res = await api.post("/ai/chat", { message: text, session_id: sessionId });
      setSessionId(res.data.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I couldn't process that. Please try again." }]);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-2xl">
      <div className="mb-4">
        <h1 className="font-display font-semibold text-2xl text-ink">AI Assistant</h1>
        <p className="text-muted text-sm mt-0.5">
          Ask about your own spending, budget, or savings — grounded in your real data.
          {aiEnabled === false && " (Running in rule-based mode — no LLM API key configured.)"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto bg-white border border-line rounded-lg p-5 space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-muted mb-3">Try asking:</p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="block w-full text-left text-sm border border-line rounded px-3 py-2 hover:border-forest/40 hover:bg-forest/5 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                m.role === "user" ? "bg-forest text-white" : "bg-paper border border-line text-ink"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && <div className="text-sm text-muted">FinMate AI is thinking…</div>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your finances…"
          className="flex-1 border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
        />
        <button
          type="submit"
          disabled={sending}
          className="bg-forest text-white rounded px-4 py-2 text-sm font-medium hover:bg-forest-light disabled:opacity-60"
        >
          Send
        </button>
      </form>
      <p className="text-xs text-muted mt-2">
        FinMate AI provides general guidance based on your data — it is not a licensed financial advisor.
      </p>
    </div>
  );
}
