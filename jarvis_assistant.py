"""The brain: an agentic tool loop with JARVIS's personality.

Two interchangeable backends:
- OllamaJarvis (default): free, runs a local model via Ollama. Private,
  no API key, no cost.
- ClaudeJarvis: uses the Claude API (paid) for the smartest responses.
  Picked automatically when ANTHROPIC_API_KEY is set.

Override with JARVIS_BACKEND=ollama|claude. Pick the local model with
JARVIS_MODEL (default "llama3.2").
"""

import datetime
import os
import platform
import re

from jarvis_tools import ALL_TOOLS

SYSTEM_PROMPT = f"""You are JARVIS, a personal AI assistant inspired by the one \
in Iron Man. You are running on the user's {platform.system()} computer and \
speaking with Akshay, whom you address as "Sir" (sparingly, not every sentence).

Personality: calm, dry British wit, unfailingly competent, concise. A touch of \
gentle sarcasm is welcome; verbosity is not.

Your replies are often spoken aloud by a text-to-speech engine, so:
- Keep responses short — one to three sentences unless asked for detail.
- No markdown, no bullet lists, no emoji. Plain spoken English only.
- Numbers and units spoken naturally ("about four gigabytes", not "4.2GB").

You have tools to control this computer: open apps and websites, check system \
status, search the web, set timers, and run shell commands (the user approves \
each command). Use them when the request calls for action rather than talk; \
answer directly, without tools, when the request is just conversation. \
If a request is ambiguous, make the obvious choice rather than interrogating \
the user. Today's date: {datetime.date.today().strftime("%B %d, %Y")}."""

MAX_TOOL_ROUNDS = 8


class OllamaJarvis:
    """Free local backend via Ollama (https://ollama.com)."""

    def __init__(self) -> None:
        import ollama

        self.ollama = ollama
        self.model = os.environ.get("JARVIS_MODEL", "llama3.2")
        self.tool_map = {fn.__name__: fn for fn in ALL_TOOLS}
        self.history: list = []

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *self.history]

        reply = "Done."
        for _ in range(MAX_TOOL_ROUNDS):
            response = self.ollama.chat(model=self.model, messages=messages, tools=ALL_TOOLS)
            message = response.message
            messages.append(message)

            if not message.tool_calls:
                # Some models (e.g. qwen3) emit <think> blocks — strip them.
                reply = re.sub(r"<think>.*?</think>", "", message.content or "",
                               flags=re.DOTALL).strip() or "Done."
                break

            for call in message.tool_calls:
                fn = self.tool_map.get(call.function.name)
                if fn is None:
                    result = f"Unknown tool: {call.function.name}"
                else:
                    try:
                        result = fn(**(call.function.arguments or {}))
                    except Exception as exc:  # noqa: BLE001 — feed failures back to the model
                        result = f"Tool error: {exc}"
                messages.append({"role": "tool", "tool_name": call.function.name,
                                 "content": str(result)})

        self.history = [m for m in messages[1:]]  # keep everything after the system prompt
        if len(self.history) > 40:
            self.history = self.history[-30:]
        return reply


class ClaudeJarvis:
    """Claude API backend (needs ANTHROPIC_API_KEY; paid)."""

    MODEL = "claude-opus-5-5"

    def __init__(self) -> None:
        import anthropic
        from anthropic import beta_tool

        self.client = anthropic.Anthropic()
        self.tools = [beta_tool(fn) for fn in ALL_TOOLS]
        self.history: list[dict] = []

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        runner = self.client.beta.messages.tool_runner(
            model=self.MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=self.history,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        final = runner.until_done()

        if final.stop_reason == "refusal":
            reply = "I'm afraid I can't help with that one, Sir."
        else:
            reply = " ".join(
                block.text for block in final.content if block.type == "text"
            ).strip() or "Done."

        self.history.append({"role": "assistant", "content": reply})
        if len(self.history) > 40:
            self.history = self.history[-30:]
        return reply


def make_jarvis():
    """Pick a backend: JARVIS_BACKEND wins; else Claude if a key is set; else Ollama."""
    backend = os.environ.get("JARVIS_BACKEND", "").strip().lower()
    if backend == "claude" or (not backend and os.environ.get("ANTHROPIC_API_KEY")):
        return ClaudeJarvis()
    return OllamaJarvis()
