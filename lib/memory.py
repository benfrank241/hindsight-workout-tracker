"""Hindsight client wrapper for workout tracking."""

import os
import json

import streamlit as st
from hindsight_client import Hindsight

from .models import WorkoutPlan

BANK_ID = os.getenv("BANK_ID", "workout-tracker")
BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888")

BANK_MISSION = """Track weightlifting workouts: exercises, sets, reps, weights,
RPE, personal records, muscle groups trained, energy levels, soreness, recovery
notes, training preferences (split type, favorite lifts), and strength goals.
Always preserve specific numbers (weights, sets, reps) and associate them with
exercise names and dates."""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "exercises": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "sets": {"type": "integer"},
                    "reps": {"type": "string"},
                    "weight": {"type": "string"},
                    "rest_seconds": {"type": "integer"},
                    "notes": {"type": "string"},
                },
                "required": ["name", "sets", "reps", "weight"],
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["title", "exercises"],
}


@st.cache_resource
def get_client() -> Hindsight:
    return Hindsight(base_url=BASE_URL)


def init_bank() -> None:
    """Create the workout bank with mission (idempotent)."""
    client = get_client()
    client.create_bank(bank_id=BANK_ID, name="Workout Tracker", mission=BANK_MISSION)


def log_workout(content: str) -> None:
    """Retain a workout log entry."""
    client = get_client()
    client.retain(bank_id=BANK_ID, content=content, tags=["workout"])


def recall_context(query: str) -> str:
    """Recall relevant memories and return as formatted context string."""
    client = get_client()
    response = client.recall(bank_id=BANK_ID, query=query, budget="low", tags=["workout"])
    if not response.results:
        return ""
    lines = []
    for r in response.results:
        lines.append(f"- {r.text}")
    return "\n".join(lines)


def generate_plan(query: str) -> WorkoutPlan:
    """Generate a structured workout plan via reflect."""
    client = get_client()
    response = client.reflect(
        bank_id=BANK_ID,
        query=query,
        budget="mid",
        response_schema=PLAN_SCHEMA,
        tags=["workout"],
    )
    data = response.structured_output
    if isinstance(data, str):
        data = json.loads(data)
    return WorkoutPlan(**data)


def ask_insight(query: str) -> str:
    """Ask a question about progress/recovery via reflect."""
    client = get_client()
    response = client.reflect(
        bank_id=BANK_ID,
        query=query,
        budget="mid",
        tags=["workout"],
    )
    return response.answer


def save_completed_plan(plan: WorkoutPlan, completed: dict[int, bool], actual_weights: dict[int, str]) -> None:
    """Build a summary of a completed plan and retain it."""
    lines = [f"Completed workout: {plan.title}"]
    for i, ex in enumerate(plan.exercises):
        if not completed.get(i):
            continue
        weight = actual_weights.get(i, ex.weight)
        lines.append(f"- {ex.name}: {ex.sets}x{ex.reps} @ {weight}")
    skipped = [ex.name for i, ex in enumerate(plan.exercises) if not completed.get(i)]
    if skipped:
        lines.append(f"Skipped: {', '.join(skipped)}")

    client = get_client()
    client.retain(bank_id=BANK_ID, content="\n".join(lines), tags=["workout", "plan"])
