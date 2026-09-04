"""
actions/copilot_watcher.py — Proactive Screen Watcher / Copilot Mode for ULTRON

Provides continuous active perception:
When enabled, periodically inspects the user's screen (every 45–60s)
to detect code tracebacks, terminal errors, or blocked states, and offers
proactive hints without needing explicit prompts.
"""

from __future__ import annotations

import base64
import threading
import time
from typing import Callable, Optional

from utils.env import get_api_key
from core.sfx import play_sfx
from actions.screen_processor import _capture_screen


class CopilotWatcher:
    """Background screen monitor that watches for errors and provides proactive guidance."""

    def __init__(self):
        self.enabled = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_alert_time = 0.0
        self.cooldown_seconds = 180  # Max 1 proactive prompt every 3 minutes
        self.interval_seconds = 45

    def toggle(self, state: bool | None = None, player=None, speak: Callable[[str], None] | None = None) -> str:
        """Enable or disable active copilot screen watching."""
        if state is None:
            self.enabled = not self.enabled
        else:
            self.enabled = state

        if self.enabled:
            self._stop_event.clear()
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._watch_loop,
                    args=(player, speak),
                    daemon=True,
                    name="UltronCopilotWatcher"
                )
                self._thread.start()
            play_sfx("startup")
            msg = "Copilot Active Perception mode is now ENGAGED. I will silently monitor your screen for errors, sir."
        else:
            self._stop_event.set()
            play_sfx("toggle")
            msg = "Copilot Active Perception mode has been STANDING DOWN."

        if player:
            player.write_log(f"👁️ [COPILOT] {msg}")
        return msg

    def _watch_loop(self, player=None, speak: Callable[[str], None] | None = None):
        """Background observation cycle."""
        while not self._stop_event.is_set():
            time.sleep(self.interval_seconds)
            if not self.enabled:
                break

            now = time.monotonic()
            if now - self._last_alert_time < self.cooldown_seconds:
                continue

            try:
                # Capture primary screen
                img_bytes, mime_type = _capture_screen(monitor=1)
                analysis = self._inspect_frame(img_bytes, mime_type)

                if analysis and analysis.get("requires_action"):
                    alert_text = analysis.get("message", "")
                    self._last_alert_time = time.monotonic()
                    play_sfx("listening")

                    if player:
                        player.write_log(f"👁️ [COPILOT DETECTED]: {alert_text}")
                    if speak:
                        speak(f"Sir, excuse the interruption. {alert_text}")

            except Exception as e:
                # Passive monitor should never crash the main application
                pass

    def _inspect_frame(self, img_bytes: bytes, mime_type: str) -> dict | None:
        """Evaluate screen frame via Gemini."""
        try:
            from google import genai
            from google.genai import types

            key = get_api_key("gemini_api_key")
            if not key:
                return None
            client = genai.Client(api_key=key)

            prompt = (
                "You are ULTRON Copilot observing the user's screen in the background. "
                "Determine if the user is facing a critical syntax error, uncaught traceback, "
                "or failing build that they might need help with. "
                "If YES and it is important, respond with JSON: "
                "{\"requires_action\": true, \"message\": \"Short 1-sentence observation and fix hint.\"} "
                "If everything is normal, working, or casual browsing, respond with: "
                "{\"requires_action\": false}"
            )

            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            text = (res.text or "").strip()
            if "{" in text and "}" in text:
                clean = text[text.find("{"):text.rfind("}") + 1]
                import json
                return json.loads(clean)
        except Exception:
            return None
        return None


# Global singleton instance
_COPILOT_INSTANCE = CopilotWatcher()


def copilot_control(parameters: dict, player=None, speak: Callable[[str], None] | None = None) -> str:
    """Tool handler for enabling/disabling copilot mode."""
    action = parameters.get("action", "toggle").lower().strip()
    if action in ("enable", "on", "start", "activate"):
        return _COPILOT_INSTANCE.toggle(True, player=player, speak=speak)
    elif action in ("disable", "off", "stop", "deactivate"):
        return _COPILOT_INSTANCE.toggle(False, player=player, speak=speak)
    else:
        return _COPILOT_INSTANCE.toggle(None, player=player, speak=speak)
