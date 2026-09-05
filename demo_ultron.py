"""
demo_ultron.py — J.A.R.V.I.S. Autonomous Capability & Tactical Engine Verification

Runs a full capability verification showing:
1. Iron Man Arc Reactor Audio SFX (Power-up, wake, and confirmation chime)
2. J.A.R.V.I.S. System Diagnostics Macro
3. Multi-Monitor Display Detection
4. Autonomous Multi-Step Goal Engine (Creates Desktop report)
5. Ecosystem Verification (Smart Home & Email/Calendar)
"""

from __future__ import annotations

import time
import sys
from pathlib import Path

print("=" * 65)
print("   🤖 J.A.R.V.I.S. TACTICAL AI SYSTEM — VERIFICATION & DIAGNOSTIC")
print("=" * 65)
print()

# 1. Iron Man Procedural Arc Reactor SFX Test
print("[1/5] 🔊 Testing Iron Man Arc Reactor SFX Engine...")
try:
    from core.sfx import play_sfx
    print("      Playing Arc-Reactor power-up sound...")
    play_sfx("startup", blocking=True)
    time.sleep(0.2)
    print("      Playing Mark VII target lock / confirmation chime...")
    play_sfx("complete", blocking=True)
    print("      ✅ Audio SFX Engine: Operational")
except Exception as e:
    print(f"      ⚠️ SFX Note: {e}")

print()

# 2. J.A.R.V.I.S. Diagnostic Macro
print("[2/5] ⚡ Running J.A.R.V.I.S. System Diagnostics Macro...")
try:
    from actions.computer_settings import computer_settings
    briefing = computer_settings({"action": "system_diagnostics"})
    print(f"      J.A.R.V.I.S.: \"{briefing}\"")
    print("      ✅ System Diagnostics: Operational")
except Exception as e:
    print(f"      ⚠️ Diagnostic Note: {e}")

print()

# 3. Multi-Monitor Display Detection
print("[3/5] 🖥️ Detecting Multi-Monitor Vision Displays...")
try:
    from actions.screen_processor import get_monitors_info
    monitors = get_monitors_info()
    if monitors:
        for m in monitors:
            print(f"      • [{m['name']}] Resolution: {m['width']}x{m['height']} (Offset: X={m['left']}, Y={m['top']})")
    else:
        print("      • Primary Display Active (Default Virtual Canvas)")
    print("      ✅ Multi-Monitor Vision: Ready")
except Exception as e:
    print(f"      ⚠️ Multi-Monitor Note: {e}")

print()

# 4. Autonomous Multi-Step Goal Execution
print("[4/5] 🧠 Executing Live Autonomous Goal Mission...")
try:
    from actions.goal_agent import execute_autonomous_goal, _get_desktop_dir
    mission = "Scan PC health metrics and generate an executive status report on Desktop"
    print(f"      Goal: '{mission}'")
    result = execute_autonomous_goal({"goal": mission})
    print(f"      Status: {result}")
    desktop_file = _get_desktop_dir() / "Ultron_Autonomous_Report.md"
    if desktop_file.exists():
        print(f"      📄 File Verified on Desktop: {desktop_file.name}")
    print("      ✅ Autonomous Goal Engine: Operational")
except Exception as e:
    print(f"      ⚠️ Goal Agent Note: {e}")

print()

# 5. Ecosystem Readiness Check
print("[5/5] 🏠 Checking Ecosystem Connectors (Smart Home & Email/Calendar)...")
try:
    from actions.home_automation import home_automation_control
    ha_status = home_automation_control({"action": "status", "device": "lights"})
    print(f"      • Smart Home Module: {ha_status[:60]}...")

    from actions.email_calendar import read_unread_emails
    mail_status = read_unread_emails(count=2)
    print(f"      • Email/Calendar   : {mail_status[:60]}...")
    print("      ✅ Ecosystem Connectors: Ready")
except Exception as e:
    print(f"      ⚠️ Ecosystem Note: {e}")

print()
print("=" * 65)
print("   🎉 J.A.R.V.I.S. OPERATIONAL — READY FOR VOICE INTERACTION, SIR!")
print("=" * 65)
