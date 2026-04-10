"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth, SignInButton, UserButton } from "@clerk/nextjs";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Send, Bot, User, Sparkles, Loader2, Copy, Check } from "lucide-react";

type Message = { role: "user" | "ai"; content: string; id: number };

const CodeBlock = ({ inline, className, children, ...props }: any) => {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : "text";

  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (!inline && match) {
    return (
      <div className="my-5 rounded-xl overflow-hidden shadow-md bg-[#282c34] border border-slate-700/50 font-sans">
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800/80 text-slate-300 border-b border-slate-700/80">
          <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">{language}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 hover:text-white transition-colors p-1 rounded-md"
            title="Copy Code"
          >
            {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
            <span className="text-[11px] font-medium">{copied ? "Copied!" : "Copy"}</span>
          </button>
        </div>
        <SyntaxHighlighter
          style={oneDark}
          language={language}
          PreTag="div"
          customStyle={{ margin: 0, padding: '1.25rem', background: 'transparent', fontSize: '13px' }}
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      </div>
    );
  }

  return (
    <code className="bg-slate-100 text-pink-600 px-1.5 py-0.5 rounded text-[13px] font-mono border border-slate-200" {...props}>
      {children}
    </code>
  );
};

export default function Home() {
  const { userId, isLoaded } = useAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const askAI = async () => {
    if (!input.trim() || loading) return;

    const newMsg: Message = { role: "user", content: input, id: Date.now() };
    setMessages((prev) => [...prev, newMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: newMsg.content, context_name: "gemini_api_docs" }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: data.answer || "No response.", id: Date.now() }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Error connecting to AI backend. Ensure the server is running on port 8000.", id: Date.now() }
      ]);
    }
    setLoading(false);
  };

  if (!mounted) {
    return <main className="min-h-screen bg-slate-50" />;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 bg-slate-50 text-slate-900 overflow-hidden relative">

      {/* Background Orbs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-400/20 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-pulse pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-400/20 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-pulse pointer-events-none" />

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-6xl flex justify-between items-center p-5 mx-auto mb-6 relative z-10 sticky top-4 rounded-2xl border border-slate-200/60 bg-white/70 backdrop-blur-xl shadow-sm"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-purple-600 to-blue-600 rounded-xl shadow-md">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">
            ChromaDB RAG
          </h1>
        </div>
        <div>
          {userId ? (
            <UserButton />
          ) : (
            <SignInButton mode="modal">
              <button className="px-5 py-2 text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors rounded-full shadow-sm">
                Log In
              </button>
            </SignInButton>
          )}
        </div>
      </motion.header>

      {/* Chat Area */}
      <div className="flex-1 w-full max-w-5xl flex flex-col gap-6 overflow-y-auto px-4 pb-36 no-scrollbar relative z-10 scroll-smooth" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center h-full text-center mt-20"
            >
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6 shadow-inner border border-purple-200">
                <Bot className="w-10 h-10 text-purple-600" />
              </div>
              <h2 className="text-2xl font-semibold text-slate-800">How can I help you?</h2>
              <p className="text-md mt-3 text-slate-500 max-w-md">Ask me anything about ChromaDB's documentation. Try: "How do I instantiate a client vector store?"</p>
            </motion.div>
          )}

          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 15, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} w-full`}
            >
              <div className={`flex gap-3 w-full ${msg.role === "user" ? "flex-row-reverse max-w-[85%] sm:max-w-[75%]" : "flex-row max-w-full sm:max-w-[95%]"}`}>
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm ${msg.role === "user" ? "bg-blue-600" : "bg-purple-600"}`}>
                  {msg.role === "user" ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                </div>
                <div className={`px-6 py-5 rounded-2xl md:text-[15px] text-sm shadow-sm leading-relaxed flex-1 min-w-0 overflow-x-auto ${msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm whitespace-pre-wrap"
                    : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm"
                  }`}>
                  {msg.role === "ai" ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc ml-6 mb-4 space-y-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal ml-6 mb-4 space-y-2">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-6 border-b border-slate-200 pb-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold mb-3 mt-5">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-md font-bold mb-2 mt-4">{children}</h3>,
                        a: ({ href, children }) => <a href={href} className="text-blue-600 hover:text-blue-800 hover:underline transition-colors">{children}</a>,
                        strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
                        blockquote: ({ children }) => <blockquote className="border-l-4 border-slate-300 pl-4 py-1 italic text-slate-600 mb-4 bg-slate-50">{children}</blockquote>,
                        pre: ({ children }) => <>{children}</>,
                        code: CodeBlock as any
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </motion.div>
          ))}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start w-full"
            >
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm bg-purple-600">
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-white border border-slate-200 rounded-tl-sm flex items-center gap-2 shadow-sm">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input Form */}
      <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-slate-50 via-slate-50/95 to-transparent pt-12 z-20 flex justify-center">
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="w-full max-w-4xl relative"
        >
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-purple-200 to-blue-200 rounded-full blur opacity-60 group-hover:opacity-100 transition duration-500"></div>
            <div className="relative flex items-center bg-white border border-slate-200 rounded-full p-2 pr-3 shadow-lg">
              <input
                className="flex-1 bg-transparent px-6 py-4 md:text-[17px] outline-none text-slate-800 placeholder-slate-400 w-full"
                value={input}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), askAI())}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about the documentation..."
                disabled={loading}
              />
              <button
                onClick={askAI}
                disabled={loading || !input.trim()}
                className="p-3.5 bg-purple-600 rounded-full text-white font-bold hover:bg-purple-700 disabled:opacity-50 transition-all ml-2 shadow-sm"
              >
                <Send className={`w-5 h-5 ${input.trim() && !loading ? "translate-x-[2px] -translate-y-[2px]" : ""} transition-transform`} />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
