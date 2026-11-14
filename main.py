"""JARVIS — personal AI assistant.

Usage:
    python main.py            # voice mode if available, else text mode
    python main.py --text     # force text mode
    python main.py --no-wake  # voice mode without the "jarvis" wake word

Backends (see README): free local model via Ollama by default; the Claude
API is used automatically if ANTHROPIC_API_KEY is set.
"""

import os
import sys

WAKE_WORD = "jarvis"
EXIT_PHRASES = {"exit", "quit", "goodbye", "shut down", "shutdown", "go to sleep"}


def check_ollama() -> bool:
    """True if the Ollama server is reachable and the chosen model is pulled."""
    model = os.environ.get("JARVIS_MODEL", "llama3.2")
    try:
        import ollama
    except ImportError:
        print("The 'ollama' Python package is missing. Run: pip install -r requirements.txt")
        return False
    try:
        names = [m.model for m in ollama.list().models]
    except Exception:  # noqa: BLE001 — any failure means the server isn't up
        print("Ollama isn't running. Install it from https://ollama.com/download,")
        print(f"then run:  ollama pull {model}")
        print("(The Ollama app runs the server automatically once installed.)")
        return False
    if not any(n.startswith(model) for n in names):
        print(f"Model '{model}' isn't downloaded yet. Run:  ollama pull {model}")
        return False
    return True


def text_mode(jarvis) -> None:
    print("JARVIS online (text mode). Type 'exit' to quit.\n")
    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in EXIT_PHRASES:
            print("JARVIS: Goodbye, Sir.")
            break
        reply = jarvis.ask(user_text)
        print(f"JARVIS: {reply}\n")


def voice_mode(jarvis, use_wake_word: bool = True) -> None:
    from jarvis_voice import listen, speak

    greeting = "JARVIS online. How may I help?"
    print(f"JARVIS: {greeting}")
    if use_wake_word:
        print(f'(Say "{WAKE_WORD}" followed by your request, e.g. "Jarvis, what time is it?")')
    speak(greeting)

    while True:
        heard = listen()
        if not heard:
            continue
        print(f"You: {heard}")

        lowered = heard.lower()
        if use_wake_word:
            if WAKE_WORD not in lowered:
                continue
            # Strip everything up to and including the wake word.
            heard = heard[lowered.index(WAKE_WORD) + len(WAKE_WORD):].lstrip(" ,.!?") or "hello"
            lowered = heard.lower()

        if lowered.strip(" .!") in EXIT_PHRASES:
            speak("Goodbye, Sir.")
            break

        reply = jarvis.ask(heard)
        print(f"JARVIS: {reply}\n")
        speak(reply)


def main() -> None:
    using_claude = bool(os.environ.get("ANTHROPIC_API_KEY")) or \
        os.environ.get("JARVIS_BACKEND", "").lower() == "claude"
    if not using_claude and not check_ollama():
        sys.exit(1)

    from jarvis_assistant import make_jarvis

    jarvis = make_jarvis()
    backend = type(jarvis).__name__.replace("Jarvis", "")
    print(f"[backend: {backend}]")

    force_text = "--text" in sys.argv
    use_wake = "--no-wake" not in sys.argv

    if not force_text:
        try:
            from jarvis_voice import voice_available

            if voice_available():
                voice_mode(jarvis, use_wake_word=use_wake)
                return
            print("Voice dependencies or microphone not available — falling back to text mode.")
            print("See README.md to enable voice.\n")
        except Exception as exc:  # noqa: BLE001 — voice is best-effort; text mode always works
            print(f"Voice mode failed ({exc}) — falling back to text mode.\n")

    text_mode(jarvis)


if __name__ == "__main__":
    main()
