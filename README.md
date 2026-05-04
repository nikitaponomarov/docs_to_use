# Docs to use

A full-stack RAG (Retrieval-Augmented Generation) application that turns any library's documentation into a queryable knowledge base.

Point it at a docs URL — it scrapes, chunks, and embeds the content automatically. From that point on you can ask questions in natural language, or paste your code to check it against the docs for deprecated functions, removed methods, and outdated patterns — and get a rewritten version using the current API.

---

## Features

- **Documentation Q&A** — ask anything about a library and get answers backed by its official docs
- **Deprecated code check** — paste a code snippet and get a list of deprecated functions, removed methods, and outdated patterns based on the actual docs
- **Automatic rewriting** — optionally receive a fully migrated version of your code using the current API
- **Multi-provider AI** — switch between Google Gemini and a local Ollama model per request
- **Self-learning** — new libraries are scraped and embedded in the background on first query; no manual ingestion step
- **Persistent storage** — raw content stored in SQLite, vector index in ChromaDB; re-starts don't re-scrape

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Next.js Frontend (Clerk auth, React Markdown, Framer Motion)    │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼─────────────────────────────────────┐
│  FastAPI  (rate-limited REST API)                                 │
│  ┌─────────────┐   ┌──────────────────────────────────────────┐  │
│  │ Orchestrator│   │ ModelHandler                             │  │
│  │             │   │  ├─ Gemini (google-genai)                │  │
│  │  scrape ──► │──►│  └─ Ollama (local, via REST)             │  │
│  │  embed  ──► │   └──────────────────────────────────────────┘  │
│  │  ask    ──► │                                                  │
│  │  deprecated►│                                                  │
│  └──────┬──────┘                                                  │
│         │                                                         │
│  ┌──────▼──────┐   ┌──────────────┐   ┌─────────────────────┐   │
│  │   SQLite    │   │   ChromaDB   │   │   Jina AI Reader    │   │
│  │ (raw pages) │   │ (embeddings) │   │ (web scraping)      │   │
│  └─────────────┘   └──────────────┘   └─────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**Data flow for a new library:**
1. First query arrives with a `url` field
2. Jina AI fetches the main page and all sub-pages within the same domain
3. Raw markdown is stored in SQLite
4. Content is chunked (markdown-header-aware) and embedded into ChromaDB
5. Subsequent queries hit ChromaDB directly — no re-scraping

---

## API Reference

### `POST /api/ask`

Ask a natural-language question about a library.

```json
{
  "query": "How do I create a persistent ChromaDB client?",
  "context_name": "chroma_docs",
  "url": "https://docs.trychroma.com",
  "ai": {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "base_url": "http://localhost:11434"
  },
  "embed": {
    "model_name": "mxbai-embed-large",
    "url": "http://localhost:11434/api/embeddings"
  }
}
```

> `url` is only required the first time a `context_name` is used. Subsequent requests omit it.

**Response**
```json
{
  "status": "success",
  "answer": "..."
}
```

If the library is being learned for the first time, the response is:
```json
{
  "status": "learning",
  "answer": "Learning from chroma_docs documentation. Please try again in a moment."
}
```

---

### `POST /api/deprecated`

Analyze a code snippet for deprecated API usage.

```json
{
  "code": "client = chromadb.Client()\nclient.create_collection('my_collection')",
  "context_name": "chroma_docs",
  "rewrite": true,
  "ai": {
    "provider": "gemini",
    "model": "gemini-2.5-flash"
  }
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | string | — | The code snippet to analyze |
| `context_name` | string | — | Library context (must already be learned) |
| `rewrite` | boolean | `true` | `true` returns rewritten code; `false` lists deprecated usages only |

**Response**
```json
{
  "status": "success",
  "answer": "## Deprecated Findings\n...\n## Rewritten Code\n..."
}
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) running locally (for embedding and/or local inference)
- A Gemini API key (for cloud inference)
- A Jina AI API key (for web scraping)

### Backend

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd docs_to_use

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Fill in GEMINI_API_KEY and JINA_API_KEY

# 5. Pull an embedding model (Ollama)
ollama pull mxbai-embed-large

# 6. Start the API server
uvicorn api:app --reload --port 8000
```

### Frontend

```bash
cd my-ai-frontend

# Install dependencies
npm install

# Set environment variables
cp .env.local.example .env.local
# Fill in your Clerk publishable and secret keys

# Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

### Backend (`.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `JINA_API_KEY` | Jina AI API key for web scraping |

### Frontend (`my-ai-frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key |

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com) — REST API with rate limiting via `slowapi`
- [ChromaDB](https://docs.trychroma.com) — local vector database
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/) — markdown-aware chunking
- [Google Gemini](https://ai.google.dev) (`google-genai`) — cloud AI inference
- [Ollama](https://ollama.com) — local AI inference and embeddings
- [Jina AI Reader](https://jina.ai/reader/) — clean markdown extraction from web pages
- SQLite — persistent raw content storage

**Frontend**
- [Next.js 16](https://nextjs.org) + TypeScript
- [Tailwind CSS v4](https://tailwindcss.com)
- [Clerk](https://clerk.com) — authentication
- [Framer Motion](https://www.framer.com/motion/) — animations
- [React Markdown](https://github.com/remarkjs/react-markdown) + [react-syntax-highlighter](https://github.com/react-syntax-highlighter/react-syntax-highlighter)

---

## Adding a New Library to the UI

Open [my-ai-frontend/src/app/page.tsx](my-ai-frontend/src/app/page.tsx) and add an entry to the `LIBRARIES` array:

```ts
{
  context_name: "fastapi_docs",   // passed to the backend as context_name
  label: "FastAPI",
  description: "Modern Python web framework",
  color: "from-teal-500 to-emerald-500",
  accent: "bg-teal-500",
}
```

The backend will scrape and learn the library automatically on the first query that includes a `url`.

---

## License

MIT
