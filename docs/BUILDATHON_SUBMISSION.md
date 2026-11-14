# TradeSense AI — Startup Buildathon India 2026 Submission
**Track:** AI & Cloud Innovation for Financial Inclusion & Risk Protection  
**Target Audience:** 10M+ Indian Retail F&O Traders (NSE/BSE)

---

## 1. Executive Summary & Problem Statement

### The Problem:
* **The SEBI Fact**: According to SEBI's official study on retail F&O trading, **93% of individual retail traders incur net losses**, with average losses exceeding ₹1.25 lakh per trader.
* **The Root Cause**: Retail traders do not lose money because of lack of market information; they lose due to **emotional discipline failures**:
  1. **Revenge Trading**: Rapidly placing consecutive trades immediately after a loss to "recover capital", leading to catastrophic drawdowns.
  2. **Over-Leveraging**: Allocating 20% to 50%+ of total portfolio equity to high-decay options contracts.
  3. **Complex Filing Asymmetry**: Inability to quickly parse 50+ page corporate announcements and quarterly earnings releases in regional languages.

### The Solution:
**TradeSense AI** is a low-latency, SEBI-compliant AI Trading Co-Pilot and Risk-Intelligence Platform built on **Google Cloud** and **Google Vertex AI**. It serves as an active guardian that monitors trading tilt in real-time, calculates institutional probabilities, backtests user strategies in natural language, and digests earnings in vernacular Indian languages.

---

## 2. Google AI & Cloud Competitive Advantage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRADESENSE AI VALUE STACK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Gemini 1.5 Flash  │ Ultra-low latency streaming (TTFT < 1s) for real-    │
│                      │ time Put-Call Ratio (PCR) analytics & calm nudges.   │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 2. Gemini 1.5 Pro    │ 2M+ token multimodal reasoning digesting 50-page     │
│                      │ corporate filings & management interview transcripts.│
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 3. Vertex AI Agent   │ Autonomous trade book auditing & revenge-trading     │
│    Builder           │ circuit breaker enforcement.                         │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 4. Cloud Memorystore │ <50ms caching of live Indian indices (NIFTY/BANKNIFTY)│
│    (Redis)           │ to eliminate redundant API calls during market spikes.│
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 5. Google Cloud Run  │ Serverless auto-scaling (0-100+ instances) for peak  │
│                      │ volume at 9:15 AM IST market open & 3:30 PM close.   │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 3. Core Features Built & Verified

### Feature 1: The "Discipline & Risk" Engine
* **Revenge Trading Detector**: Flags users when they execute >5 trades in 30 minutes following a loss.
* **AI Calm Nudge**: Uses Gemini 1.5 Flash to synthesize a calm, rational one-sentence reminder in Hindi/English:
  > *"You are exhibiting signs of revenge trading with rapid consecutive orders after a loss. Take a 15-minute emotional cooldown to reset."*
* **Dynamic Discipline Scorecard (0–100)**: Real-time quantification of trader discipline penalizing over-leveraging and tilt.

### Feature 2: Conversational No-Code Backtesting
* Users type trade ideas in plain language (*"Buy Nifty when 5-min candle crosses above 200 EMA with 1:2 risk-reward"*).
* Simulates execution over **3,000 historical 5-minute candles** in milliseconds.
* Generates institutional risk metrics: **Win Rate (%)**, **Profit Factor**, **Max Drawdown (%)**, **Sharpe Ratio**, and interactive **Equity Curve**.

### Feature 3: Vernacular Multimodal Filing Analyzer
* Parses complex quarterly results and YouTube executive interview transcripts.
* Extracts precise operating margin changes in basis points (e.g. `+90 bps EBITDA expansion` or `-120 bps contraction`).
* Generates bulleted executive summaries in **Hindi (हिन्दी)**, **Gujarati (ગુજરાતી)**, **Marathi (मराठी)**, and **English**.

### Feature 4: Strict SEBI Regulatory Guardrails
* Mandatory statutory disclaimer appended to all LLM outputs.
* Automated pre-flight regex & intent filter that intercepts and rejects direct speculative stock tips and price targets.

---

## 4. Live Hackathon Demo Walkthrough (3-Minute Pitch Script)

| Time | Screen / Tab | Action & Speaker Script |
| :--- | :--- | :--- |
| **0:00 - 0:40** | **Top Bar & Ticker** | *"Judges, 93% of Indian retail traders lose money in F&O due to emotional revenge trading. TradeSense AI solves this. Notice our top bar: streaming live NIFTY, BANKNIFTY, and Put-Call Ratio at sub-50ms latency via Google Cloud Memorystore."* |
| **0:40 - 1:20** | **Risk Guardian Tab** | *Click "Trigger Revenge Trading Demo": "Watch what happens when a trader executes 5 rapid loss-recovery trades. Our behavioral engine immediately engages a 15-minute cooldown and Gemini Flash speaks to the trader in English and Hindi to de-escalate tilt."* |
| **1:20 - 2:00** | **AI Copilot Tab** | *Type "What does NIFTY PCR 1.15 mean?" and then "Should I buy Call option?": "Notice the sub-second streaming response with live market context, and see how our SEBI guardrail strictly refuses direct stock tips to protect compliance."* |
| **2:00 - 2:40** | **Backtesting Tab** | *Click "200 EMA Reversal" and hit Execute Backtest: "In under 500ms, our vectorized engine compiles plain English into a quantitative strategy over 3,000 bars, plotting the equity curve and Sharpe ratio."* |
| **2:40 - 3:00** | **Research Desk Tab** | *Select Tata Motors Q3 filing in Hindi: "Finally, Gemini 1.5 Pro digests complex filings, isolates the +90 bps EBITDA margin impact, and explains it in Hindi, Gujarati, or Marathi for regional traders."* |

---

## 5. Deployment & Execution
```bash
# 1. Local Run
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --port 8000

# 2. Automated Test Suite (27/27 Tests)
PYTHONPATH=backend pytest backend/tests/

# 3. Google Cloud Run Deploy
./scripts/deploy_cloud_run.sh
```
