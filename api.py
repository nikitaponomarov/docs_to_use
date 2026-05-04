from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from main import Orchestrator, DEFAULT_EMBED_MODEL, DEFAULT_EMBED_URL, DEFAULT_AI_PROVIDER, DEFAULT_AI_MODEL, DEFAULT_AI_BASE_URL

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


class AIConfig(BaseModel):
    provider: str = DEFAULT_AI_PROVIDER   # "gemini" | "ollama"
    model: str = DEFAULT_AI_MODEL         # e.g. "gemini-2.5-flash" or "llama3"
    base_url: str = DEFAULT_AI_BASE_URL   # only used for ollama


class EmbedConfig(BaseModel):
    model_name: str = DEFAULT_EMBED_MODEL  # e.g. "mxbai-embed-large" or "nomic-embed-text"
    url: str = DEFAULT_EMBED_URL


class UserQuery(BaseModel):
    query: str
    context_name: str
    url: str | None = None          # required when learning a new library
    ai: AIConfig = AIConfig()
    embed: EmbedConfig = EmbedConfig()


@app.post("/api/ask")
@limiter.limit("10/minute")
async def ask_ai(request: Request, user_query: UserQuery, background_tasks: BackgroundTasks):
    if not orchestrator.has_context(user_query.context_name):
        if not user_query.url:
            raise HTTPException(status_code=400, detail="url is required to learn a new library")
        background_tasks.add_task(
            orchestrator.scrape_and_learn,
            user_query.url,
            user_query.context_name,
            user_query.embed.model_name,
            user_query.embed.url,
        )
        return {
            "status": "learning",
            "answer": f"Learning from {user_query.context_name} documentation. Please try again in a moment.",
        }
    try:
        response = orchestrator.ask(
            user_query.query,
            user_query.context_name,
            ai_provider=user_query.ai.provider,
            ai_model=user_query.ai.model,
            ai_base_url=user_query.ai.base_url,
        )
        return {"status": "success", "answer": response}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal AI Error")
