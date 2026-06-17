from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.external import external_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.rate_limit import limiter

app = FastAPI(
    title="Swan API",
    version="0.1.0",
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router,      prefix="/api/v1")
app.include_router(external_router, prefix="/api/external")


@app.get("/health")
async def health():
    return {"status": "ok"}
