"""Local browser chat; gr.State gives every browser session a separate ADK identity."""
import gradio as gr
from google.adk.sessions import InMemorySessionService
from examples.first_agent.agent import root_agent
from examples.runtime import new_identity, run_turn

# The service is shared, identities are not. In-memory history disappears on restart.
sessions = InMemorySessionService()


async def respond(message, history, identity):
    identity = identity or new_identity()
    try:
        answer, _ = await run_turn(root_agent, message, identity, sessions)
        return answer or "No final answer was returned.", identity
    except Exception as error:
        return f"The request failed ({type(error).__name__}). Check the local terminal and API configuration.", identity


def build_app():
    with gr.Blocks(title="ADK order assistant") as demo:
        identity = gr.State(value=new_identity)
        gr.Markdown("# Order assistant\nEach browser session has its own conversation. This is a local teaching app.")
        chat = gr.ChatInterface(fn=respond, additional_inputs=[identity], additional_outputs=[identity])
        chat.chatbot.clear(fn=new_identity, outputs=[identity], queue=False)
    return demo


if __name__ == "__main__":
    build_app().queue().launch(server_name="127.0.0.1", share=False)
