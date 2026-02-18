# Hindsight Workout Tracker

A mobile-friendly Streamlit web app that tracks your weightlifting workouts using [Hindsight](https://github.com/hindsight-ai/hindsight) for persistent memory. Log workouts conversationally, generate personalized plans, and track your progress over time.

## Features

- **Log** — Chat with a coach to log workouts and ask questions. Your history is remembered across sessions.
- **Plan** — Generate personalized workout plans based on your training history. Follow along with checkboxes and log completion.
- **Insights** — Ask about squat progress, weekly volume, recovery status, PRs, and more.

## Quick Start

### Prerequisites

- Python 3.11+
- A running [Hindsight](https://hindsight.ing) API (or `hindsight-all` installed locally)
- An OpenAI API key

### Setup

```bash
# Clone
git clone https://github.com/benfrank241/hindsight-workout-tracker.git
cd hindsight-workout-tracker

# Install deps
pip install .

# Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# Run (starts hindsight-api + streamlit)
./run.sh
```

Or run manually:

```bash
# Terminal 1: start Hindsight API
hindsight-api

# Terminal 2: start the app
streamlit run app.py
```

Open http://localhost:8501 on your phone or browser.

## How It Works

| Feature | Hindsight API |
|---------|--------------|
| Log a workout | `retain()` with `tags=["workout"]` |
| Chat context | `recall()` before each coach response |
| Generate plan | `reflect(response_schema=...)` for structured JSON |
| Track progress | `reflect()` for natural-language insights |
| Complete plan | `retain()` the summary with `tags=["workout", "plan"]` |

## Stack

- **Streamlit** — UI
- **Hindsight** — Long-term memory (retain/recall/reflect)
- **OpenAI** — Chat coaching (gpt-4o-mini)
- **Pydantic** — Structured workout plan models
