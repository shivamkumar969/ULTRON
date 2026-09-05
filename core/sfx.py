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
    """Generate normalized float32 mono waveform for authentic Iron Man J.A.R.V.I.S. HUD audio."""
    sr = SAMPLE_RATE

    if sfx_type == "wake":
        # Iron Man HUD wake: instant crisp glass-harmonic ping + warm arc-reactor spool
        dur_ping = 0.28
        t = np.linspace(0, dur_ping, int(sr * dur_ping), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 16)
        # Frequencies tuned to musical D6 / A5 holographic interval
        wave = (
            0.55 * np.sin(2 * np.pi * 1174.66 * t)
            + 0.30 * np.sin(2 * np.pi * 1760.0 * t)
            + 0.15 * np.sin(2 * np.pi * 587.33 * t)
        )
        return (wave * env * 0.35).astype(np.float32)

    elif sfx_type == "listening":
        # Crisp holographic HUD micro-blip (Iron Man helmet interface click)
        duration = 0.08
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 45)
        wave = 0.7 * np.sin(2 * np.pi * 1318.51 * t) + 0.3 * np.sin(2 * np.pi * 2637.0 * t)
        return (wave * env * 0.28).astype(np.float32)

    elif sfx_type == "thinking":
        # Subdued cybernetic resonance pulse (subtle arc hum)
        duration = 0.25
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        lfo = 0.5 * (1.0 + np.sin(2 * np.pi * 8.0 * t))
        env = np.sin(np.pi * (t / duration))
        wave = (0.7 * np.sin(2 * np.pi * 440.0 * t) + 0.3 * np.sin(2 * np.pi * 880.0 * t)) * lfo
        return (wave * env * 0.20).astype(np.float32)

    elif sfx_type == "complete":
        # Iconic Mark VII 3-tone ascending triad chime (D5 -> A5 -> D6)
        tone_dur = 0.075
        chunks = []
        for f in (587.33, 880.0, 1174.66):
            t = np.linspace(0, tone_dur, int(sr * tone_dur), endpoint=False, dtype=np.float32)
            env = np.exp(-t * 18)
            tone = 0.65 * np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * (f * 2) * t)
            chunks.append(tone * env)
        wave = np.concatenate(chunks)
        return (wave * 0.32).astype(np.float32)

    elif sfx_type == "error":
        # Tactical warning blip (descending minor third)
        tone_dur = 0.10
        chunks = []
        for f in (620.0, 440.0):
            t = np.linspace(0, tone_dur, int(sr * tone_dur), endpoint=False, dtype=np.float32)
            env = np.exp(-t * 22)
            tone = 0.75 * np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * (f * 1.5) * t)
            chunks.append(tone * env)
        wave = np.concatenate(chunks)
        return (wave * 0.35).astype(np.float32)

    elif sfx_type == "startup":
        # Cinematic Arc Reactor Power-Up:
        # Stage 1: Deep electromagnetic sub-bass swell (60Hz -> 240Hz)
        # Stage 2: Brilliant crystal harmonic chime
        dur1 = 0.45
        t1 = np.linspace(0, dur1, int(sr * dur1), endpoint=False, dtype=np.float32)
        freq_sweep = np.geomspace(65, 320, len(t1))
        env1 = np.sin(np.pi * (t1 / dur1) ** 0.7)
        stage1 = (0.75 * np.sin(2 * np.pi * freq_sweep * t1) + 0.25 * np.sin(2 * np.pi * freq_sweep * 2 * t1)) * env1

        dur2 = 0.25
        t2 = np.linspace(0, dur2, int(sr * dur2), endpoint=False, dtype=np.float32)
        env2 = np.exp(-t2 * 12)
        stage2 = (0.6 * np.sin(2 * np.pi * 1174.66 * t2) + 0.4 * np.sin(2 * np.pi * 1760.0 * t2)) * env2

        wave = np.concatenate([stage1 * 0.4, stage2 * 0.35])
        return wave.astype(np.float32)

    else:  # toggle
        duration = 0.06
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 50)
        wave = np.sin(2 * np.pi * 880.0 * t)
        return (wave * env * 0.25).astype(np.float32)


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
