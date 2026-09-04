"""
core/sfx.py — Procedural Sci-Fi Audio SFX Engine for ULTRON

Synthesizes high-tech robotic/Jarvis sound effects mathematically via NumPy
and sounddevice. Requires zero external audio assets, runs entirely in memory,
and executes non-blockingly on background threads.
"""

from __future__ import annotations

import math
import threading
from typing import Literal
import numpy as np

try:
    import sounddevice as sd
    _SD_OK = True
except ImportError:
    _SD_OK = False

SAMPLE_RATE = 24_000
SFX_TYPE = Literal["wake", "listening", "thinking", "complete", "error", "startup", "toggle"]


def _synthesize_waveform(sfx_type: SFX_TYPE) -> np.ndarray:
    """Generate normalized float32 mono waveform for the requested sound effect."""
    sr = SAMPLE_RATE

    if sfx_type == "wake":
        # Cinematic rising dual-harmonic sweep (150Hz -> 650Hz + harmonic overtone)
        duration = 0.45
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        freq_main = np.geomspace(160, 720, len(t))
        freq_harm = freq_main * 1.5
        env = np.sin(np.pi * (t / duration) ** 0.6)  # smooth swell
        wave = 0.6 * np.sin(2 * np.pi * freq_main * t) + 0.3 * np.sin(2 * np.pi * freq_harm * t)
        return (wave * env * 0.4).astype(np.float32)

    elif sfx_type == "listening":
        # Short, crisp holographic high-tech ping (880Hz -> 1320Hz)
        duration = 0.12
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 35)  # rapid decay
        wave = 0.7 * np.sin(2 * np.pi * 950 * t) + 0.3 * np.sin(2 * np.pi * 1425 * t)
        return (wave * env * 0.35).astype(np.float32)

    elif sfx_type == "thinking":
        # Subdued cybernetic resonance pulse (440Hz modulated by 12Hz)
        duration = 0.3
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        lfo = 0.5 * (1 + np.sin(2 * np.pi * 14 * t))
        env = np.sin(np.pi * (t / duration))
        wave = np.sin(2 * np.pi * 520 * t) * lfo
        return (wave * env * 0.25).astype(np.float32)

    elif sfx_type == "complete":
        # Ascending 3-tone holographic confirmation chime (600Hz -> 900Hz -> 1200Hz)
        tone_dur = 0.07
        chunks = []
        for f in (640, 960, 1280):
            t = np.linspace(0, tone_dur, int(sr * tone_dur), endpoint=False, dtype=np.float32)
            env = np.exp(-t * 20)
            tone = 0.7 * np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * (f * 1.5) * t)
            chunks.append(tone * env)
        wave = np.concatenate(chunks)
        return (wave * 0.35).astype(np.float32)

    elif sfx_type == "error":
        # Descending dual-tone metallic alert (480Hz -> 240Hz)
        tone_dur = 0.12
        chunks = []
        for f in (480, 310):
            t = np.linspace(0, tone_dur, int(sr * tone_dur), endpoint=False, dtype=np.float32)
            env = np.exp(-t * 18)
            tone = 0.7 * np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * (f * 1.25) * t)
            chunks.append(tone * env)
        wave = np.concatenate(chunks)
        return (wave * 0.4).astype(np.float32)

    elif sfx_type == "startup":
        # Power-up pulse: deep bass drop followed by crisp metallic sweep
        duration = 0.6
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        freq = np.geomspace(90, 880, len(t))
        env = np.sin(np.pi * (t / duration) ** 0.5)
        wave = 0.7 * np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * (freq * 2) * t)
        return (wave * env * 0.45).astype(np.float32)

    else:  # toggle
        duration = 0.08
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 40)
        wave = np.sin(2 * np.pi * 750 * t)
        return (wave * env * 0.3).astype(np.float32)


# Pre-synthesized waveform cache
_SFX_CACHE: dict[str, np.ndarray] = {}


def _init_cache():
    for st in ("wake", "listening", "thinking", "complete", "error", "startup", "toggle"):
        try:
            _SFX_CACHE[st] = _synthesize_waveform(st)
        except Exception:
            pass


_init_cache()


def play_sfx(sfx_type: SFX_TYPE, blocking: bool = False) -> None:
    """
    Play a sci-fi sound effect asynchronously on a background daemon thread.
    Zero latency, safe across all threads.
    """
    if not _SD_OK:
        return

    def _worker():
        try:
            audio = _SFX_CACHE.get(sfx_type)
            if audio is None:
                audio = _synthesize_waveform(sfx_type)
            sd.play(audio, SAMPLE_RATE)
            if blocking:
                sd.wait()
        except Exception:
            pass

    if blocking:
        _worker()
    else:
        threading.Thread(target=_worker, daemon=True, name=f"sfx-{sfx_type}").start()
