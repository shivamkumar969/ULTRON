# GEMINI & AI AGENT CONTEXT — ULTRON

This repository is **ULTRON**, an advanced AI Desktop Assistant and autonomous OS agent.

## Quick AI Orientation

- **Language & Runtime**: Python 3.10+ on Windows 10/11 (with cross-platform abstractions in `utils/env.py`).
- **Primary AI Model**: `models/gemini-2.5-flash-native-audio-preview-12-2025` using the `google-genai` SDK for bidirectional real-time audio and function calling.
- **GUI Framework**: PyQt6 + PyQt6-WebEngine (renders on the Main Thread).
- **Automation Backends**: Playwright (Browsers), PyAutoGUI & pywinauto (Desktop), MSS & OpenCV (Vision), psutil (Hardware telemetry).
- **Remote Web Server**: FastAPI + Uvicorn on Port 8000.

## Critical Invariants & Rules for AI Agents

1. **Subprocess Windows Patch**: Do NOT remove the monkey-patch of `_subprocess.Popen` at the top of `main.py`. It suppresses distracting console windows on Windows.
2. **Never Block the Main Qt Thread**: Any long-running or external call inside `main.py` MUST be wrapped in `await loop.run_in_executor(None, ...)`.
3. **No Hallucinated Actions**: Never claim to have performed an action without dispatching the real underlying tool in `TOOL_REGISTRY`.
4. **Tool Creation Protocol**: Follow the 3-step checklist documented in [AGENTS.md](file:///f:/ultronmain-main/AGENTS.md):
   - Logic in `actions/<tool_name>.py`
   - Schema in `core/tool_declarations.py`
   - Dispatch handler in `main.py`'s `TOOL_REGISTRY`
5. **Log All Code Modifications**: Keep [CHANGELOG.md](file:///f:/ultronmain-main/CHANGELOG.md) updated under `[Unreleased]` for every feature or fix introduced.

For comprehensive architectural diagrams and concurrency details, refer to [ARCHITECTURE.md](file:///f:/ultronmain-main/ARCHITECTURE.md).
