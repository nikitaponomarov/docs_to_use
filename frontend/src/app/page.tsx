"use client";
import { useState, useRef, useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth, SignInButton, UserButton } from "@clerk/nextjs";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Copy,
  Check,
  Search,
  BookOpen,
  ChevronDown,
  X,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// Library registry – add new libraries here, backend does the rest
// ─────────────────────────────────────────────────────────────────────────────
const LIBRARIES: {
  context_name: string;
  label: string;
  description: string;
  color: string;
  accent: string;
}[] = [
    {
      context_name: "chroma_docs",
      label: "ChromaDB",
      description: "Vector database & embeddings",
      color: "from-violet-600 to-purple-600",
      accent: "bg-violet-600",
    },
    {
      context_name: "gemini_api_docs",
      label: "Gemini API",
      description: "Google AI generative model API",
      color: "from-blue-500 to-cyan-500",
      accent: "bg-blue-500",
    },
  ];

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
type Message = {
  role: "user" | "ai";
  content: string;
  id: number;
  library?: string;
};

// ─────────────────────────────────────────────────────────────────────────────
// Code block component
// ─────────────────────────────────────────────────────────────────────────────
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
          <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            {language}
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 hover:text-white transition-colors p-1 rounded-md"
            title="Copy Code"
          >
            {copied ? (
              <Check size={14} className="text-green-400" />
            ) : (
              <Copy size={14} />
            )}
            <span className="text-[11px] font-medium">
              {copied ? "Copied!" : "Copy"}
            </span>
          </button>
        </div>
        <SyntaxHighlighter
          style={oneDark}
          language={language}
          PreTag="div"
          customStyle={{
            margin: 0,
            padding: "1.25rem",
            background: "transparent",
            fontSize: "13px",
          }}
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      </div>
    );
  }

  return (
    <code
      className="bg-slate-100 text-pink-600 px-1.5 py-0.5 rounded text-[13px] font-mono border border-slate-200"
      {...props}
    >
      {children}
    </code>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Library Picker Dropdown
// Renders the menu via a Portal into document.body so it is never trapped
// inside a parent stacking context (e.g. the sticky header).
// ─────────────────────────────────────────────────────────────────────────────
function LibraryPicker({
  selected,
  onSelect,
}: {
  selected: (typeof LIBRARIES)[number];
  onSelect: (lib: (typeof LIBRARIES)[number]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [menuStyle, setMenuStyle] = useState<React.CSSProperties>({});
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [portalReady, setPortalReady] = useState(false);

  // Portal can only render client-side
  useEffect(() => { setPortalReady(true); }, []);

  // Position the portal dropdown relative to the trigger button
  useEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setMenuStyle({
      position: "fixed",
      top: rect.bottom + 8,
      right: window.innerWidth - rect.right,
      zIndex: 99999,
      minWidth: 288,
    });
  }, [open]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (triggerRef.current && triggerRef.current.contains(target)) return;
      setOpen(false);
      setSearch("");
    };
    // Defer so the opening click doesn't immediately close
    const id = window.setTimeout(() => document.addEventListener("mousedown", handler), 0);
    return () => { window.clearTimeout(id); document.removeEventListener("mousedown", handler); };
  }, [open]);

  const filtered = useMemo(
    () =>
      LIBRARIES.filter(
        (l) =>
          l.label.toLowerCase().includes(search.toLowerCase()) ||
          l.description.toLowerCase().includes(search.toLowerCase())
      ),
    [search]
  );

  const menu = (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -6, scale: 0.97 }}
          transition={{ duration: 0.15 }}
          style={menuStyle}
          className="w-72 bg-white rounded-2xl shadow-2xl border border-slate-200/80 overflow-hidden"
        >
          {/* Search */}
          <div className="p-3 border-b border-slate-100">
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-xl border border-slate-200 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100 transition-all">
              <Search size={14} className="text-slate-400 shrink-0" />
              <input
                id="library-search-input"
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search libraries..."
                className="flex-1 bg-transparent text-sm text-slate-700 placeholder-slate-400 outline-none"
              />
              {search && (
                <button onMouseDown={() => setSearch("")}>
                  <X size={12} className="text-slate-400 hover:text-slate-600" />
                </button>
              )}
            </div>
          </div>

          {/* Library list */}
          <div className="max-h-60 overflow-y-auto py-2 px-2">
            {filtered.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-sm">No libraries found</div>
            ) : (
              filtered.map((lib) => {
                const isActive = lib.context_name === selected.context_name;
                return (
                  <button
                    key={lib.context_name}
                    id={`library-option-${lib.context_name}`}
                    // Use onMouseDown so selection fires before the outside-click
                    // handler closes the dropdown
                    onMouseDown={(e) => {
                      e.preventDefault();
                      onSelect(lib);
                      setOpen(false);
                      setSearch("");
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 cursor-pointer ${isActive
                        ? "bg-slate-100 text-slate-900"
                        : "hover:bg-slate-50 text-slate-700"
                      }`}
                  >
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${lib.color} flex items-center justify-center shrink-0 shadow-sm`}>
                      <BookOpen size={14} className="text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold truncate">{lib.label}</div>
                      <div className="text-[11px] text-slate-400 truncate">{lib.description}</div>
                    </div>
                    {isActive && (
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-br ${lib.color} shrink-0`} />
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50/60">
            <p className="text-[11px] text-slate-400">
              {LIBRARIES.length} librar{LIBRARIES.length === 1 ? "y" : "ies"} available
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        id="library-picker-btn"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 bg-white/80 hover:bg-white hover:shadow-md transition-all duration-200 text-sm font-medium text-slate-700 shadow-sm backdrop-blur-sm"
      >
        <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-br ${selected.color} shadow-sm`} />
        <BookOpen size={14} className="text-slate-500" />
        <span className="max-w-[120px] truncate">{selected.label}</span>
        <ChevronDown
          size={13}
          className={`text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {/* Portal renders directly into body — no stacking context issues */}
      {portalReady && createPortal(menu, document.body)}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
  const { userId, isLoaded } = useAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLib, setSelectedLib] = useState(LIBRARIES[0]);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // When user switches library mid-conversation, add a small context-switch note
  const handleSelectLib = (lib: (typeof LIBRARIES)[number]) => {
    if (lib.context_name === selectedLib.context_name) return;
    setSelectedLib(lib);
    if (messages.length > 0) {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: `Switched to **${lib.label}** documentation. Ask me anything about ${lib.label}!`,
          id: Date.now(),
          library: lib.context_name,
        },
      ]);
    }
  };

  const askAI = async () => {
    if (!input.trim() || loading) return;

    const newMsg: Message = {
      role: "user",
      content: input,
      id: Date.now(),
      library: selectedLib.context_name,
    };
    setMessages((prev) => [...prev, newMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: newMsg.content,
          context_name: selectedLib.context_name,
        }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: data.answer || "No response.",
          id: Date.now(),
          library: selectedLib.context_name,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content:
            "Error connecting to the AI backend. Make sure the server is running on port 8000.",
          id: Date.now(),
        },
      ]);
    }
    setLoading(false);
  };

  if (!mounted) {
    return <main className="min-h-screen bg-slate-50" />;
  }

  // Dynamic gradient accent based on selected lib
  const accentGradient = selectedLib.color;

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 bg-slate-50 text-slate-900 overflow-hidden relative">
      {/* Background Orbs — change color with selected lib */}
      <div
        key={selectedLib.context_name + "-orb1"}
        className={`absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br ${accentGradient} opacity-10 rounded-full mix-blend-multiply filter blur-[120px] pointer-events-none transition-all duration-700`}
      />
      <div
        key={selectedLib.context_name + "-orb2"}
        className={`absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-to-br ${accentGradient} opacity-10 rounded-full mix-blend-multiply filter blur-[120px] pointer-events-none transition-all duration-700`}
      />

      {/* ── Header ── */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-6xl flex justify-between items-center p-4 mx-auto mb-6 relative z-10 sticky top-4 rounded-2xl border border-slate-200/60 bg-white/70 backdrop-blur-xl shadow-sm"
      >
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div
            className={`p-2 bg-gradient-to-tr ${accentGradient} rounded-xl shadow-md transition-all duration-500`}
          >
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600 leading-tight">
              Docs RAG
            </h1>
            <p className="text-[11px] text-slate-400 leading-none">
              Powered by {selectedLib.label}
            </p>
          </div>
        </div>

        {/* Right side: lib picker + auth */}
        <div className="flex items-center gap-3">
          <LibraryPicker selected={selectedLib} onSelect={handleSelectLib} />
          {userId ? (
            <UserButton />
          ) : (
            <SignInButton mode="modal">
              <button
                id="sign-in-btn"
                className="px-4 py-2 text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors rounded-full shadow-sm"
              >
                Log In
              </button>
            </SignInButton>
          )}
        </div>
      </motion.header>

      {/* ── Chat Area ── */}
      <div
        className="flex-1 w-full max-w-5xl flex flex-col gap-6 overflow-y-auto px-4 pb-36 relative z-10 scroll-smooth"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        <AnimatePresence>
          {/* Empty state */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center h-full text-center mt-16"
            >
              <div
                className={`w-20 h-20 bg-gradient-to-br ${accentGradient} rounded-full flex items-center justify-center mb-6 shadow-xl transition-all duration-500`}
              >
                <Bot className="w-9 h-9 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800">
                Ask about {selectedLib.label}
              </h2>
              <p className="text-sm mt-3 text-slate-500 max-w-md leading-relaxed">
                {selectedLib.description}. Switch libraries from the picker in the
                header to query a different documentation set.
              </p>

              {/* Library pills */}
              <div className="flex flex-wrap justify-center gap-2 mt-8">
                {LIBRARIES.map((lib) => (
                  <button
                    key={lib.context_name}
                    id={`empty-lib-pill-${lib.context_name}`}
                    onClick={() => handleSelectLib(lib)}
                    className={`px-4 py-2 rounded-full text-sm font-medium border transition-all duration-200 ${lib.context_name === selectedLib.context_name
                        ? `bg-gradient-to-r ${lib.color} text-white border-transparent shadow-md`
                        : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:shadow-sm"
                      }`}
                  >
                    {lib.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Messages */}
          {messages.map((msg) => {
            const msgLib = LIBRARIES.find(
              (l) => l.context_name === msg.library
            );
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 15, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.28 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                  } w-full`}
              >
                <div
                  className={`flex gap-3 w-full ${msg.role === "user"
                      ? "flex-row-reverse max-w-[85%] sm:max-w-[75%]"
                      : "flex-row max-w-full sm:max-w-[95%]"
                    }`}
                >
                  {/* Avatar */}
                  <div
                    className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm bg-gradient-to-br ${msg.role === "user"
                        ? "from-slate-600 to-slate-800"
                        : msgLib
                          ? msgLib.color
                          : accentGradient
                      } transition-all duration-300`}
                  >
                    {msg.role === "user" ? (
                      <User className="w-5 h-5 text-white" />
                    ) : (
                      <Bot className="w-5 h-5 text-white" />
                    )}
                  </div>

                  {/* Bubble */}
                  <div
                    className={`px-6 py-5 rounded-2xl md:text-[15px] text-sm shadow-sm leading-relaxed flex-1 min-w-0 overflow-x-auto ${msg.role === "user"
                        ? "bg-gradient-to-br from-slate-700 to-slate-900 text-white rounded-tr-sm whitespace-pre-wrap"
                        : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm"
                      }`}
                  >
                    {msg.role === "ai" ? (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => (
                            <p className="mb-4 last:mb-0">{children}</p>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc ml-6 mb-4 space-y-2">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal ml-6 mb-4 space-y-2">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => <li>{children}</li>,
                          h1: ({ children }) => (
                            <h1 className="text-xl font-bold mb-3 mt-6 border-b border-slate-200 pb-2">
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 className="text-lg font-bold mb-3 mt-5">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-md font-bold mb-2 mt-4">
                              {children}
                            </h3>
                          ),
                          a: ({ href, children }) => (
                            <a
                              href={href}
                              className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                            >
                              {children}
                            </a>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold text-slate-900">
                              {children}
                            </strong>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-slate-300 pl-4 py-1 italic text-slate-600 mb-4 bg-slate-50">
                              {children}
                            </blockquote>
                          ),
                          pre: ({ children }) => <>{children}</>,
                          code: CodeBlock as any,
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
            );
          })}

          {/* Loading indicator */}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start w-full"
            >
              <div className="flex gap-3">
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm bg-gradient-to-br ${accentGradient}`}
                >
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-white border border-slate-200 rounded-tl-sm flex items-center gap-2 shadow-sm">
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{
                      animationDelay: "0ms",
                      background: "var(--bounce-color, #7c3aed)",
                    }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{
                      animationDelay: "150ms",
                      background: "var(--bounce-color, #7c3aed)",
                    }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{
                      animationDelay: "300ms",
                      background: "var(--bounce-color, #7c3aed)",
                    }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endOfMessagesRef} />
      </div>

      {/* ── Input Bar ── */}
      <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-slate-50 via-slate-50/95 to-transparent pt-12 z-20 flex justify-center">
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="w-full max-w-4xl relative"
        >
          {/* Selected library badge above input */}
          <div className="flex justify-center mb-2">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold text-white bg-gradient-to-r ${accentGradient} shadow-sm transition-all duration-500`}
            >
              <BookOpen size={10} />
              {selectedLib.label} docs
            </span>
          </div>

          <div className="relative group">
            <div
              className={`absolute -inset-1 bg-gradient-to-r ${accentGradient} rounded-full blur opacity-30 group-hover:opacity-60 transition duration-500`}
            />
            <div className="relative flex items-center bg-white border border-slate-200 rounded-full p-2 pr-3 shadow-lg">
              <input
                id="chat-input"
                className="flex-1 bg-transparent px-6 py-4 md:text-[17px] outline-none text-slate-800 placeholder-slate-400 w-full"
                value={input}
                onKeyDown={(e) =>
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  (e.preventDefault(), askAI())
                }
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Ask about ${selectedLib.label}...`}
                disabled={loading}
              />
              <button
                id="send-btn"
                onClick={askAI}
                disabled={loading || !input.trim()}
                className={`p-3.5 bg-gradient-to-br ${accentGradient} rounded-full text-white font-bold disabled:opacity-40 transition-all duration-300 ml-2 shadow-sm hover:scale-105 active:scale-95`}
              >
                <Send
                  className={`w-5 h-5 ${input.trim() && !loading
                      ? "translate-x-[2px] -translate-y-[2px]"
                      : ""
                    } transition-transform`}
                />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
