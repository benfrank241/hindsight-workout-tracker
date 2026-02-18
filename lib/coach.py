"""OpenAI chat engine with Hindsight memory context injection."""

import os

from openai import OpenAI

SYSTEM_PROMPT = """You are a concise, knowledgeable strength coach. The user is
at the gym on their phone — keep responses SHORT (2-3 sentences max unless they
ask for detail).

You have access to the user's workout history below. Reference specific numbers
(weights, sets, reps, PRs) when relevant. Be encouraging but data-driven.

If the user logs a workout, confirm what you recorded in one line. If they ask
a question, answer directly using their history.

MEMORY CONTEXT:
{memory_context}"""

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def get_response(user_message: str, memory_context: str, chat_history: list[dict]) -> str:
    """Get a chat response from OpenAI with memory context injected."""
    client = _get_client()

    system = SYSTEM_PROMPT.format(memory_context=memory_context or "No workout history yet.")

    messages = [{"role": "system", "content": system}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )

    return response.choices[0].message.content
