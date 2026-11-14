# JARVIS — Personal AI Assistant

A lightweight, Iron-Man-style voice assistant for your own machine. **Free by
default**: it runs a local AI model through [Ollama](https://ollama.com) — no
API key, no cost, fully private. Talk to it ("Jarvis, open Spotify") or type
to it, and it can:

- **Open apps and websites** on your computer
- **Check system status** — CPU, memory, disk, battery
- **Search the web** and answer from the results
- **Set timers** and announce them out loud
- **Run shell commands** — each one shown to you for approval first
- **Chat** — with JARVIS's dry British personality

Works on macOS, Windows, and Linux. Text mode needs nothing but Python and
Ollama; voice mode adds a microphone and two extra packages.

## Setup (free)

1. **Python 3.10+** installed.

2. **Install Ollama** from <https://ollama.com/download> (the app runs the
   local AI server automatically), then download a model:

   ```bash
   ollama pull llama3.2
   ```

   `llama3.2` (2 GB) runs on almost any machine. If you have 16 GB+ RAM or a
   GPU, `ollama pull qwen2.5:7b` or `llama3.1:8b` is noticeably smarter —
   then set `JARVIS_MODEL=qwen2.5:7b` before running.

3. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run it:**

   ```bash
   python main.py --text
   ```

## Optional: Claude backend (paid, smartest)

Local models are free but make mistakes with tools; the Claude API is far more
capable. If you ever want it: `pip install anthropic`, get a key at
<https://platform.claude.com/>, and set it —

```powershell
# Windows PowerShell (persists in new terminals)
setx ANTHROPIC_API_KEY "sk-ant-..."
```

```bash
# macOS / Linux (add to ~/.zshrc or ~/.bashrc to persist)
export ANTHROPIC_API_KEY="sk-ant-..."
```

JARVIS uses Claude automatically when the key is set. Force a backend with
`JARVIS_BACKEND=ollama` or `JARVIS_BACKEND=claude`.

## Enabling voice

```bash
# macOS first:   brew install portaudio
# Linux first:   sudo apt install portaudio19-dev espeak
pip install -r requirements-voice.txt
python main.py
```

Say **"Jarvis"** followed by your request: *"Jarvis, what's my CPU usage?"*,
*"Jarvis, open YouTube"*, *"Jarvis, set a timer for 10 minutes for the oven"*.
Say *"Jarvis, go to sleep"* to exit. Use `--no-wake` to skip the wake word, or
`--text` to type instead of talk.

- Speech-to-text uses the free Google Web Speech endpoint via the
  `SpeechRecognition` package (needs internet; fine for personal use).
- Text-to-speech uses your OS's built-in voices via `pyttsx3` (offline). It
  picks a British voice if one is installed — on macOS, add "Daniel" under
  System Settings → Accessibility → Spoken Content → System Voice.

## How it works

```
main.py             entry point: wake-word voice loop or text REPL
jarvis_assistant.py agentic tool loop + JARVIS personality (Ollama or Claude)
jarvis_tools.py     the tools the model can call on your machine
jarvis_voice.py     microphone input + text-to-speech output
```

Each request goes to the model with the tool list; the loop executes whatever
tools the model calls and continues until it has an answer. Safety notes:

- `run_shell_command` always prints the exact command and waits for your
  `y/N` approval before running anything.
- With the Claude backend, a server-side refusal fallback is enabled
  (`fallbacks="default"`).

## Extending it

Add a plain function to `jarvis_tools.py` with a good docstring (Google-style
`Args:` section), append it to `ALL_TOOLS`, and JARVIS can use it. Ideas:
control Spotify via its API, read your calendar, control smart lights.

## The heavyweight alternative: OpenJarvis

If you outgrow this, [OpenJarvis](https://github.com/open-jarvis/OpenJarvis)
(Stanford, 15k+ stars) is a full local-first agent framework: local models via
Ollama, Whisper speech recognition, neural TTS, scheduled agents, Telegram and
Discord channels, and thousands of importable skills. One-line install:

```bash
curl -fsSL https://open-jarvis.github.io/OpenJarvis/install.sh | bash
```

Then run `jarvis`. It's a much bigger system — this repo is the
understand-every-line version; OpenJarvis is the batteries-included one.
