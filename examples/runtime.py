"""Small Runner adapter shared by CLI and UI; each caller owns its identity."""
from uuid import uuid4
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "adk2_course"


def new_identity() -> dict[str, str]:
    return {"user_id": uuid4().hex, "session_id": uuid4().hex}


async def run_turn(agent, prompt: str, identity: dict, sessions) -> tuple[str, list]:
    session = await sessions.get_session(app_name=APP_NAME, **identity)
    if session is None:
        await sessions.create_session(app_name=APP_NAME, **identity)
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=sessions)
    messages, events = [], []
    async for event in runner.run_async(
        **identity, new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
    ):
        events.append(event)
        content = event.content
        if content and event.is_final_response():
            text = "".join(part.text or "" for part in content.parts or [])
            if text:
                messages.append(text)
    return "\n".join(messages), events


async def run_once(agent, prompt: str):
    return await run_turn(agent, prompt, new_identity(), InMemorySessionService())
