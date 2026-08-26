# TravelPlanAgent

A learning project based on Hello-Agents: a safe, command-line travel-planning agent.

## Setup

```bash
cd /Users/hanwang/Learn/agent-learning-notes/travel-plan-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with an OpenAI-compatible API key, model ID, and (if needed) base URL.

## Run

```bash
python app.py
```

Try: `Plan a relaxed three-day Kyoto trip for two people. We like food and temples.`

## Current scope

The agent asks for missing trip details and drafts itineraries. It does not use live travel data or make bookings. Future chapters will add tools, memory, evaluation, and verified external information.
