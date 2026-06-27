from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from src.infrastructure.http.rate_limit import limiter
from src.infrastructure.http.routes.deck import router as deck_router
from src.infrastructure.playwright.browser_pool import close_browser_pool
from src.infrastructure.utils.http_client import close_http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    yield
    # Shutdown
    await close_browser_pool()
    await close_http_client()


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(
        title="Moxfield Analyzer API",
        description="API para validação e análise de decks do Moxfield para o formato Kindred Wars",
        version="1.0.0",
        contact={
            "name": "Moxfield Analyzer",
        },
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_exceeded_handler)

    # CORS Configuration from environment
    cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
    origins_list = [o.strip() for o in cors_origins.split(",")] if cors_origins != "*" else ["*"]
    
    cors_methods = os.getenv("CORS_ALLOW_METHODS", "GET,POST,OPTIONS")
    methods_list = [m.strip() for m in cors_methods.split(",")]
    
    cors_headers = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization")
    headers_list = [h.strip() for h in cors_headers.split(",")]
    
    cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
    cors_max_age = int(os.getenv("CORS_MAX_AGE", "86400"))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins_list,
        allow_credentials=cors_credentials,
        allow_methods=methods_list,
        allow_headers=headers_list,
        max_age=cors_max_age,
    )

    app.include_router(deck_router)

    return app
