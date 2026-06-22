import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register ORM models, create missing tables, then align columns with older DBs
    import app.models  # noqa: F401
    from app.db.database import Base, engine
    from app.db.ensure_schema import ensure_schema

    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    logger.info("Database tables + schema check complete.")
    yield


app = FastAPI(title="Career Assistant AI", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "career-assistant-api"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# update: 2026-03-29 21:55:08.142820