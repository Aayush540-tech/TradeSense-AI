from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis_client import redis_client
from app.services.market_feed import market_feed
from app.routers import stream, chat, research, risk, backtest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tradesense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect Redis and start market ingestion feed
    logger.info("Initializing TradeSense AI Backend...")
    await redis_client.connect()
    await market_feed.start()
    yield
    # Shutdown: Cleanly close feeds and Redis pool
    logger.info("Shutting down TradeSense AI Backend...")
    await market_feed.stop()
    await redis_client.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Trading Co-Pilot & Risk-Intelligence Platform (Startup Buildathon India 2026)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration for Flutter Web and Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(stream.router)
app.include_router(chat.router)
app.include_router(research.router)
app.include_router(risk.router)
app.include_router(backtest.router)


@app.get("/health", tags=["Health"])
async def health_check():
    redis_latency = await redis_client.get_latency_ms()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "redis_connected": redis_client.is_connected,
        "redis_latency_ms": redis_latency,
        "market_feed_running": market_feed.is_running,
        "disclaimer": settings.SEBI_DISCLAIMER_TEXT,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to TradeSense AI — Low-Latency Risk Intelligence Platform",
        "docs": "/docs",
        "stream_status": "/api/v1/stream/status",
        "disclaimer": settings.SEBI_DISCLAIMER_TEXT,
    }
