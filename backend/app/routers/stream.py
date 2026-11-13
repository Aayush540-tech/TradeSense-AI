import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.market_feed import market_feed
from app.schemas.market import TickData, OptionChainSummary, MarketFeedStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stream", tags=["Market Data Streaming"])


@router.get("/status", response_model=MarketFeedStatus)
async def get_stream_status():
    """Returns telemetry on market feed connectivity, ticks per second, and cache latency."""
    return await market_feed.get_status()


@router.get("/ticks/latest", response_model=Dict[str, Optional[TickData]])
async def get_latest_ticks():
    """
    Sub-50ms endpoint retrieving current index prices directly from Redis/Memorystore.
    """
    symbols = ["NIFTY 50", "BANKNIFTY", "FINNIFTY", "SENSEX"]
    results = {}
    for s in symbols:
        results[s] = await market_feed.get_latest_tick(s)
    return results


@router.get("/option-chain", response_model=OptionChainSummary)
async def get_option_chain_summary(
    underlying: str = Query("NIFTY 50", description="Underlying index (e.g. NIFTY 50, BANKNIFTY)")
):
    """Retrieves the latest Put-Call Ratio (PCR) and ATM implied volatility metrics."""
    return await market_feed.get_latest_option_chain(underlying)


@router.websocket("/ws")
async def websocket_market_stream(websocket: WebSocket):
    """
    High-frequency WebSocket endpoint streaming live ticks and option chain events to frontend.
    """
    await websocket.accept()
    queue = await market_feed.subscribe()
    logger.info("New client connected to market stream WebSocket.")

    try:
        while True:
            # Receive broadcasted tick/option data or check for incoming ping
            msg_json = await queue.get()
            await websocket.send_text(msg_json)
    except WebSocketDisconnect:
        logger.info("Client disconnected from market stream WebSocket.")
    except Exception as e:
        logger.error(f"WebSocket streaming error: {e}")
    finally:
        market_feed.unsubscribe(queue)
