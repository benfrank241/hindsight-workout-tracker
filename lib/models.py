"""Pydantic models for workout plans."""

from pydantic import BaseModel


class PlannedExercise(BaseModel):
    name: str
    sets: int
    reps: str
    weight: str
    rest_seconds: int = 90
    notes: str = ""


class WorkoutPlan(BaseModel):
    title: str
    exercises: list[PlannedExercise]
    notes: str = ""


class ActivePlan(BaseModel):
    plan: WorkoutPlan
    completed: dict[int, bool] = {}
    actual_weights: dict[int, str] = {}
