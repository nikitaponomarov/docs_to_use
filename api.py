from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import your existing code
from main import Orchestrator 

# 1. Setup App and Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Define what data the frontend will send
class UserQuery(BaseModel):
    query: str
    context_name: str  # Set by the frontend based on user's library selection

# 4. Create the Endpoint
@app.post("/api/ask")
@limiter.limit("10/minute")
async def ask_ai(request: Request, user_query: UserQuery):
    try:
        # Run your existing RAG Orchestrator
        orchestrator = Orchestrator(user_query.query, user_query.context_name)
        response = orchestrator.run()
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal AI Error")

# To run this: uvicorn api:app --reload
