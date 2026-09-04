# AGENTS.md — AI Engineering & Contributor Guide for ULTRON

> **Target Audience**: Any AI coding agent (Antigravity, Cursor, Gemini, Claude, Copilot, ChatGPT) or human developer working on the ULTRON codebase.
> **Purpose**: Provide full operational context, architectural invariants, critical do's & don'ts, tool extension checklists, and change management standards.

---

## 1. Project Overview & Mental Model

**ULTRON** is an autonomous AI Desktop Assistant and OS automation agent powered by the **Google Gemini Live Audio/Multimodal API** (`models/gemini-2.5-flash-native-audio-preview-12-2025`). It combines real-time full-duplex conversational voice interaction with a visual HUD, wake-word activation, a remote web dashboard, and 20+ specialized execution tools.

### Core Philosophy
1. **Never Hallucinate or Fake Execution**: ULTRON must always call the appropriate tool. If the user asks to open an app, adjust volume, or inspect files, the agent MUST execute the tool rather than claiming it succeeded.
2. **Duplex Voice First**: The primary interface is bidirectional audio streaming (16kHz in, 24kHz out) with interruptibility (barge-in).
3. **No GUI Freezes**: The visual interface runs on PyQt6. The AI event loop runs on `asyncio`. Heavy blocking operations (Playwright, OpenCV, PyAutoGUI, file I/O, subprocesses) MUST be dispatched to background executor threads (`loop.run_in_executor(None, ...)`).
4. **Clean Windows Integration**: Console windows are suppressed via process-level patching (`CREATE_NO_WINDOW`). No stray cmd.exe popups should be spawned.

---

## 2. Repository Layout & Module Ownership

```
f:/ultronmain-main/
├── main.py                  # Orchestrator: Gemini Live session, tool dispatch, audio I/O loop
├── ui.py                    # PyQt6 WebEngine HUD, holographic UI, status visualizer
├── wake_service.py          # Background wake-word listener (SpeechRecognition / Vosk)
├── ULTRON_SETUP.py          # Portable environment & dependency validator
├── START_ULTRON.bat         # Main launcher script (Windows)
├── SETUP.bat                # 1-click bootstrap launcher
├── Start_ULTRON_Wake_Word.bat# Background wake service launcher
├── requirements.txt         # Python package dependencies
│
├── config/
│   ├── api_keys.json        # Active configuration (Gemini API key, user name, UI color)
│   ├── api_keys.json.example# Template configuration
│   └── jarvis.ico           # Application icon
│
├── core/
│   ├── tool_declarations.py # Gemini Function Calling JSON schemas (TOOL_DECLARATIONS)
│   ├── prompt.txt           # ULTRON core persona system instruction
│   ├── llm_client.py        # Local LLM fallback (Ollama / OpenAI-compatible servers)
│   ├── tts.py               # Local & cloud TTS engines (EdgeTTS, Kokoro, ElevenLabs)
│   ├── stt.py               # Local STT engines (faster-whisper, Vosk)
│   └── installer.py         # Sub-installer routines
│
├── actions/                 # Modular action engines (Tool implementations)
│   ├── browser_control.py   # Playwright automation (Chrome, Edge, Firefox, Brave)
│   ├── computer_control.py  # PyAutoGUI mouse/keyboard control & hotkeys
│   ├── computer_settings.py # OS settings (volume, brightness, wifi, power)
│   ├── dev_agent.py         # Autonomous multi-file project builder & auto-debugger
│   ├── code_helper.py       # Code generator, editor, runner, and explainer
│   ├── file_processor.py    # Universal multimodal file handler (OCR, PDF, CSV, media)
│   ├── file_controller.py   # Filesystem manager (CRUD, search, desktop cleanup)
│   ├── game_updater.py      # Steam & Epic Games installer, updater, and scheduler
│   ├── screen_processor.py  # Real-time screen capture & webcam vision stream
│   ├── system_monitor.py    # Telemetry collector (CPU, RAM, GPU, thermals, battery)
│   ├── proactive.py         # Silence tracker and proactive prompt generator
│   ├── send_message.py      # Messaging automation (WhatsApp Desktop, Telegram)
│   ├── reminder.py          # Windows Task Scheduler timed reminders
│   ├── web_search.py        # Web search & news fetcher (DuckDuckGo / scraping)
│   ├── youtube_video.py     # YouTube player & transcript summarizer
│   └── flight_finder.py     # Google Flights scrapper
│
├── dashboard/
│   ├── server.py            # FastAPI + Uvicorn HTTP/WebSocket dashboard server (Port 8000)
│   └── static/              # Dashboard frontend (HTML, CSS, JS, CryptoJS)
│
├── memory/
│   ├── memory_manager.py    # Long-term memory manager (long_term.json)
│   ├── config_manager.py    # Configuration loader & validator
│   ├── cmr_manager.py       # Conversational memory recall
│   └── reminder_manager.py  # Scheduled reminder storage
│
└── utils/
    └── env.py               # Cross-platform environment helpers (OS detection, paths)
```

---

## 3. Critical Architectural Invariants (DO NOT BREAK)

### A. The Windows `Popen` Patch in `main.py`
At lines 6–16 of `main.py`, `_subprocess.Popen` is globally patched to force `CREATE_NO_WINDOW`.
- **Rule**: NEVER remove or alter this patch unless specifically refactoring cross-platform behavior. Without it, every external tool call (like `pactl`, `powershell`, `netsh`) creates a disruptive blinking black terminal window on Windows.

### B. Asyncio vs. PyQt6 Thread Safety
- `main.py` runs a dedicated `asyncio` event loop in a background daemon thread.
- `ui.py` runs the Qt Application Event Loop (`QApplication.exec()`) on the **Main Thread**.
- **Rule**: NEVER call Qt GUI methods directly from the asyncio thread or background worker threads. Always emit Qt signals (`pyqtSignal`) or post events.
- **Rule**: NEVER execute blocking operations (like Playwright waits, file downloads, PyAutoGUI sleeps, heavy HTTP requests) inside the asyncio event loop thread directly. Always use:
  ```python
  await loop.run_in_executor(None, lambda: your_blocking_action(...))
  ```

### C. Gemini Live Audio Protocols
- **Microphone Stream**: 16,000 Hz, 1 channel (Mono), Float32 or Int16 PCM, chunk size 512–1024 frames.
- **Speaker Playback**: 24,000 Hz, 1 channel (Mono), 24kHz raw PCM directly streamed to `sounddevice`.
- **Interrupt Handling**: When `self.interrupt()` is called, the audio input queue is immediately drained and `self.set_speaking(False)` is triggered to restore `LISTENING` state.

### D. Memory Budget
- `memory/long_term.json` is budgeted with a hard ceiling of `MEMORY_MAX_CHARS` (default ~2200 chars).
- When adding new fields or memories, ensure `_trim_to_limit()` is preserved so prompts do not overflow token budgets.

---

## 4. How to Add a New Tool / Action (Checklist)

Whenever adding a new capability to ULTRON, follow this 3-step checklist:

### Step 1: Implement Action Logic in `actions/<new_action>.py`
Create a clean, standalone module in `actions/`:
```python
# actions/my_feature.py
def my_feature(parameters: dict, player=None) -> str:
    param1 = parameters.get("param1")
    # Perform task safely...
    if player:
        player.write_log(f"SYS: Executed my_feature with {param1}")
    return f"Successfully executed my_feature: {param1}"
```

### Step 2: Declare the Tool Schema in `core/tool_declarations.py`
Add the function specification to `TOOL_DECLARATIONS`:
```python
{
    "name": "my_feature",
    "description": "Clear instruction for Gemini when to invoke this tool.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "param1": {
                "type": "STRING",
                "description": "Description of param1"
            }
        },
        "required": ["param1"]
    }
}
```

### Step 3: Register Handler in `main.py`
In `UltronLive`:
1. Import the new action:
   ```python
   from actions.my_feature import my_feature
   ```
2. Add the async handler method:
   ```python
   async def _handle_my_feature(self, args, loop):
       r = await loop.run_in_executor(None, lambda: my_feature(parameters=args, player=self.ui))
       return r or "Done."
   ```
3. Add entry to `TOOL_REGISTRY`:
   ```python
   TOOL_REGISTRY = {
       ...
       "my_feature": _handle_my_feature,
   }
   ```

---

## 5. Coding Guidelines & Agent Rules

- **Type Annotations**: Use Python 3.10+ union syntax (`str | None`, `list[str]`) and type hints where appropriate.
- **Error Handling**: Tools must catch internal exceptions and return human-readable error strings rather than crashing the session. Return strings like `"Error executing task: <details>"`.
- **Config Handling**: Never hardcode API keys or user paths. Use `utils/env.py` or read from `config/api_keys.json`.
- **Subprocesses**: Ensure `timeout` is always specified for `subprocess.run()` calls to prevent zombie hangs.
- **Log Updates**: Whenever you introduce changes, update [CHANGELOG.md](file:///f:/ultronmain-main/CHANGELOG.md) according to the Keep a Changelog standard.
