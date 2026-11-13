import re
from typing import Optional, Tuple
from app.core.config import settings

MANDATORY_SYSTEM_PROMPT = (
    "You are a risk-management and research assistant for Indian retail traders. "
    "Do not recommend buying or selling specific securities. "
    "Provide historical data, mathematical probabilities, and risk metrics only. "
    "End financial analyses with a disclaimer."
)

VERNACULAR_INSTRUCTIONS = {
    "en": "Respond in clear, professional English.",
    "hi": "उत्तर सरल और स्पष्ट हिंदी (Hindi / Hinglish) में दें, ताकि भारतीय रिटेल ट्रेडर इसे आसानी से समझ सकें।",
    "gu": "સ્પષ્ટ અને સરળ ગુજરાતી (Gujarati) માં જવાબ આપો, જેથી ભારતીય રિટેલ ટ્રેડર્સ જોખમનું યોગ્ય વિશ્લેષણ સમજી શકે.",
    "mr": "स्पष्ट आणि सोप्या मराठीत (Marathi) उत्तर द्या, जेणेकरून भारतीय रिटेल ट्रेडर्स जोखमीचे विश्लेषण नीट समजू शकतील.",
}

# Regex patterns catching direct speculative buy/sell signals or tips
PROHIBITED_INTENT_PATTERNS = [
    r"\b(should\s+i\s+(buy|sell|short|go\s+long))\b",
    r"\b(which\s+(stock|call|put|strike)\s+to\s+buy)\b",
    r"\b(buy\s+or\s+sell)\b",
    r"\b(give\s+me\s+a?\s*(tip|call|target|trade|recommendation))\b",
    r"\b(what\s+is\s+the\s+target\s+(for|price))\b",
    r"\b(will\s+(nifty|banknifty|sensex|stock)\s+(go\s+up|crash|rally|fall))\b",
    r"\b(kon\s+sa\s+(share|stock|call|put)\s+kharide|khareedu)\b",
    r"\b(best\s+stock\s+to\s+buy\s+today)\b",
    r"\b(guaranteed\s+profit)\b",
    r"\b(jackpot\s+call)\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_INTENT_PATTERNS]


def validate_user_intent(query: str) -> Tuple[bool, Optional[str]]:
    """
    SEBI Compliance Pre-Flight Guardrail:
    Scans incoming user query for prohibited direct advice requests.
    Returns (is_compliant, refusal_message).
    """
    clean_query = query.strip()
    for pattern in COMPILED_PATTERNS:
        if pattern.search(clean_query):
            refusal_message = (
                "🛡️ **SEBI Compliance Notice**: TradeSense AI is strictly an educational and "
                "risk-intelligence copilot. Under SEBI research and advisory regulations, we do not "
                "provide direct buy/sell recommendations, stock tips, or directional price targets.\n\n"
                "**What I can do instead:**\n"
                "• Calculate current Put-Call Ratio (PCR) and Open Interest support/resistance\n"
                "• Analyze Implied Volatility (IV) and max-pain thresholds\n"
                "• Quantify position sizing risk and drawdown probabilities\n"
                "• Backtest your rule-based strategy on historical tick data\n\n"
                f"*{settings.SEBI_DISCLAIMER_TEXT}*"
            )
            return False, refusal_message

    return True, None


def inject_system_guardrail(
    user_prompt: str,
    language: str = "en",
    market_context: Optional[dict] = None
) -> str:
    """
    Constructs the full system-injected prompt to ensure compliance and context awareness.
    """
    vernacular_guide = VERNACULAR_INSTRUCTIONS.get(language, VERNACULAR_INSTRUCTIONS["en"])

    context_str = ""
    if market_context:
        context_str = (
            f"\n\n[LIVE MARKET CONTEXT (Sub-50ms Cache)]:\n"
            f"- Current NIFTY 50: {market_context.get('nifty_spot', 'N/A')} "
            f"(PCR: {market_context.get('nifty_pcr', 'N/A')}, Sentiment: {market_context.get('nifty_sentiment', 'N/A')})\n"
            f"- Current BANKNIFTY: {market_context.get('banknifty_spot', 'N/A')} "
            f"(PCR: {market_context.get('banknifty_pcr', 'N/A')}, Sentiment: {market_context.get('banknifty_sentiment', 'N/A')})\n"
            f"- ATM Straddle IV: {market_context.get('atm_iv', 'N/A')}%\n"
        )

    full_prompt = (
        f"System Guardrail: {MANDATORY_SYSTEM_PROMPT}\n"
        f"Language Directive: {vernacular_guide}\n"
        f"{context_str}\n"
        f"User Query: {user_prompt}\n\n"
        f"Crucial: Structure your answer around risk metrics, volatility, and mathematical probabilities. "
        f"Conclude your response with the following exact disclaimer text:\n"
        f"\"{settings.SEBI_DISCLAIMER_TEXT}\""
    )
    return full_prompt


def ensure_disclaimer(response_text: str) -> str:
    """
    Post-flight check: Guarantees the mandatory SEBI disclaimer is present.
    """
    disclaimer_snippet = "TradeSense AI is an educational and analytical research platform"
    if disclaimer_snippet not in response_text:
        return f"{response_text.strip()}\n\n---\n*{settings.SEBI_DISCLAIMER_TEXT}*"
    return response_text
