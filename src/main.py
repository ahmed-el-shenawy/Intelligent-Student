from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from routes import data_router, documents_router, projects_router, query_router, system_router, auth_router
from helpers import settings
from llm.LLMClient import LLMClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("🚀 App is starting up! Initializing resources...")

    app.state.generation_client = LLMClient(base_url = settings.GROQ_BASE_URL,
                                             api_key= settings.GROQ_API_KEY,
                                             model_name = settings.GROQ_MODEL)
    
    app.state.embedding_client = LLMClient(base_url = settings.OLLAMA_BASE_URL,
                                            api_key= settings.OLLAMA_API_KEY,
                                            model_name = settings.OLLAMA_MODEL)


    print("✅ Resources initialized successfully.")

    yield

    # --- Shutdown ---

    print("👋 App shutdown complete. Goodbye!")

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(query_router)
app.include_router(system_router)


# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "App is running smoothly!"}
    )