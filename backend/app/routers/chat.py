import logging
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.config import settings
from app.services.market_feed import market_feed
from app.services.gemini_service import gemini_service
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["AI Copilot & Guardrails"])


async def _get_current_market_context() -> dict:
    """Fetches sub-50ms market context from Redis for AI prompt enrichment."""
    nifty = await market_feed.get_latest_tick("NIFTY 50")
    banknifty = await market_feed.get_latest_tick("BANKNIFTY")
    chain = await market_feed.get_latest_option_chain("NIFTY 50")

    return {
        "nifty_spot": nifty.ltp if nifty else 24150.0,
        "banknifty_spot": banknifty.ltp if banknifty else 51800.0,
        "nifty_pcr": chain.pcr if chain else 1.05,
        "nifty_sentiment": chain.sentiment if chain else "NEUTRAL",
        "atm_iv": chain.atm_iv if chain else 13.5,
    }


@router.post("/stream")
async def stream_chat_endpoint(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for Gemini 1.5 Flash.
    Provides Time-to-First-Token (TTFT) < 1s with live market context & SEBI guardrails.
    """
    market_context = None
    if request.include_market_context:
        market_context = await _get_current_market_context()

    async def event_generator():
        try:
            async for chunk in gemini_service.stream_chat(
                query=request.message,
                language=request.language,
                history=request.conversation_history,
                market_context=market_context,
            ):
                # Send as clean text SSE chunks
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error in chat stream generator: {e}")
            yield f"data: Error generating analysis: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/query", response_model=ChatResponse)
async def query_chat_endpoint(request: ChatRequest):
    """
    Standard JSON endpoint for conversational risk intelligence.
    """
    start_time = time.perf_counter()
    market_context = None
    if request.include_market_context:
        market_context = await _get_current_market_context()

    full_reply = ""
    async for chunk in gemini_service.stream_chat(
        query=request.message,
        language=request.language,
        history=request.conversation_history,
        market_context=market_context,
    ):
        full_reply += chunk

    latency_ms = (time.perf_counter() - start_time) * 1000
    is_refused = "SEBI Compliance Notice" in full_reply

    return ChatResponse(
        reply=full_reply,
        disclaimer=settings.SEBI_DISCLAIMER_TEXT,
        language=request.language,
        is_refused=is_refused,
        latency_ms=round(latency_ms, 2),
        model="gemini-1.5-flash"
    )
