# CHANGELOG — ULTRON Assistant

All notable changes to the ULTRON codebase are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Instructions for AI Agents & Contributors

> [!IMPORTANT]
> Whenever you modify, add, or deprecate features in this project:
> 1. Add an entry under the `[Unreleased]` section below.
> 2. Categorize the change under:
>    - `Added` for new features or tools.
>    - `Changed` for changes in existing functionality.
>    - `Deprecated` for soon-to-be removed features.
>    - `Removed` for now removed features.
>    - `Fixed` for any bug fixes.
>    - `Security` in case of vulnerabilities or auth enhancements.
> 3. Provide concise bullets describing the file touched and the rationale.

---

## [Unreleased]

### Added
- **Procedural Sci-Fi Audio SFX Engine**: Created `core/sfx.py` synthesizing mathematical cybernetic sound cues (wake pulse, listening blip, thinking resonance, complete chime, error alert, startup power-up) via NumPy and sounddevice.
- **Autonomous Multi-Step Goal Engine**: Created `actions/goal_agent.py` with an iterative Agentic ReAct loop that deconstructs high-level missions, orchestrates tools, recovers from errors, logs real-time progress to the UI, and saves executive markdown reports to the Desktop.
- **Multi-Monitor Screen Vision**: Upgraded `actions/screen_processor.py` and `core/tool_declarations.py` to support `monitor` parameter (Display 1, Display 2, or virtual combined display) and added `get_monitors_info()`.
- **Smart Home & IoT Automation**: Created `actions/home_automation.py` with Home Assistant REST API and MQTT support to control lights, switches, AC temperature, and read sensors.
- **Email & Calendar Automation**: Created `actions/email_calendar.py` utilizing native Windows Outlook COM (`win32com`) and IMAP/SMTP fallback to read unread emails, send emails, and schedule calendar appointments hands-free.
- **Active Perception Copilot Mode**: Created `actions/copilot_watcher.py` to passively monitor screens in the background and proactively offer guidance when terminal errors or code tracebacks are detected.
- **Tool Registry Integration**: Registered all 4 new tools in `main.py`'s `TOOL_REGISTRY` and declared schemas in `core/tool_declarations.py`.

### Changed
- **Gemini Model Upgrade**: Upgraded all action engines from deprecated `gemini-2.5-flash` / `gemini-2.5-flash-lite` to Google's official `gemini-3.6-flash` (`web_search.py`, `code_helper.py`, `dev_agent.py`, `desktop.py`, `file_processor.py`, `flight_finder.py`, `youtube_video.py`, `computer_settings.py`, `computer_control.py`), and updated live audio streaming model to `models/gemini-2.5-flash-native-audio-latest`.

### Fixed
- Fixed missing `_capture_screen` import in `main.py` which would have caused a runtime `NameError` during screen vision capture.
- Fixed Python 3.10 incompatibility in `actions/screen_processor.py` by replacing `asyncio.TaskGroup` and `except*` syntax with `asyncio.gather` and standard exception handling.
- Added `from __future__ import annotations` to 14 files ensuring complete PEP 604 type annotation backward compatibility for Python 3.9 environments.
- Added safe fallback imports for `playwright` in `actions/browser_control.py` to prevent missing C++ compiler build crashes.
- Added dynamic OneDrive Desktop path resolution in `actions/goal_agent.py`.
- Replaced `asyncio.TaskGroup` in `main.py` with `asyncio.gather` and clean cancellation handling for full Python 3.9+ compatibility.
- Fixed missing `import os` in `actions/system_monitor.py` that occurred during high-memory emergency process termination.
- Fixed `.bat` launchers (`START_ULTRON.bat`, `SETUP.bat`, `Start_ULTRON_Wake_Word.bat`) encoding issues by removing non-ASCII unicode characters and enforcing CRLF formatting.
- Updated `ULTRON_SETUP.py` to allow Python 3.9 environments and generated `.ultron_setup_complete`.
- Added safe fallback imports for `sounddevice` and `google.genai` across action modules.

---

## [1.0.0] - 2026-09-04

### Added
- **Gemini Live Multimodal Engine**: Real-time bidirectional audio streaming using `gemini-2.5-flash-native-audio-preview-12-2025` at 16kHz in and 24kHz out.
- **Voice Interruption / Barge-in**: Low-latency interruption system that drains audio buffers when the user speaks over the assistant.
- **Always-on Wake Word Service**: Background listener in `wake_service.py` with multi-engine support (SpeechRecognition / Vosk) listening for "Wake up Ultron".
- **PyQt6 Holographic HUD**: Futuristic UI in `ui.py` with WebEngine support, animated audio visualizer, camera preview stream, and state indicators.
- **Remote Mobile Dashboard**: FastAPI + Uvicorn server in `dashboard/server.py` with AES-256 encrypted session tokens, mobile mic streaming, telemetry broadcasting, and remote control.
- **Autonomous Dev Agent**: Multi-file project planning, code writing, dependency resolution, error parsing, and automated 5-iteration bug fixing in `actions/dev_agent.py`.
- **Game Updater Subsystem**: Steam and Epic Games library scanner, updater, downloader, and overnight update scheduler in `actions/game_updater.py`.
- **Universal File Processor**: Multimodal processor in `actions/file_processor.py` supporting OCR, PDF extraction, Excel/CSV analysis, and audio/video manipulation.
- **Computer Vision Subsystem**: Screen capture via MSS and webcam capture via OpenCV in `actions/screen_processor.py` fed directly to Gemini Live.
- **Long-Term Memory Subsystem**: Categorized persistent memory in `memory/memory_manager.py` with automated token-limit trimming.
- **Proactive Assistant Engine**: Silence detection and contextual check-in generation in `actions/proactive.py`.
- **System Telemetry & Monitoring**: Hardware metrics collection (CPU, RAM, GPU, thermals, battery) with automated voice alerts in `actions/system_monitor.py`.
- **Desktop & OS Automation**: Full mouse/keyboard control, app launcher, volume, brightness, WiFi, and window management via PyAutoGUI and OS APIs.
- **Portable Setup Automation**: First-time automatic setup script `ULTRON_SETUP.py` with dependency resolution, Playwright Chromium installer, and batch launchers.
