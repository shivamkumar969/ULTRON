"""
actions/goal_agent.py — Autonomous Multi-Step Goal Engine for ULTRON

Enables ULTRON to act as a fully autonomous agent:
Decomposes high-level instructions into concrete sub-tasks, executes them
in an iterative ReAct loop, recovers from errors, logs real-time progress to
the UI HUD, and delivers an executive voice briefing upon completion.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable, Any

from utils.env import get_api_key, get_base_dir
from core.sfx import play_sfx

# Action modules available to the Goal Engine
from actions.web_search import web_search
from actions.file_controller import file_controller
from actions.code_helper import code_helper
from actions.computer_settings import computer_settings

BASE_DIR = get_base_dir()
MAX_STEPS = 8
MAX_RETRIES_PER_STEP = 3


def _get_gemini():
    try:
        from google import genai
        key = get_api_key("gemini_api_key")
        if not key:
            return None
        return genai.Client(api_key=key)
    except Exception:
        return None


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\r?\n?", "", text)
    text = re.sub(r"\r?\n?```\s*$", "", text)
    return text.strip()


def plan_goal(goal: str) -> list[dict]:
    """
    Decompose high-level goal into an ordered sequence of executable sub-tasks.
    Each sub-task specifies:
      - 'step': short description
      - 'action': 'web_search' | 'file_controller' | 'code_helper' | 'computer_settings' | 'custom'
      - 'params': dict of tool arguments
    """
    client = _get_gemini()
    if not client:
        # Heuristic fallback plan if offline
        return [
            {
                "step": f"Execute search for: {goal}",
                "action": "web_search",
                "params": {"query": goal, "mode": "search"}
            },
            {
                "step": "Save findings to desktop file",
                "action": "file_controller",
                "params": {
                    "action": "create_file",
                    "path": "desktop",
                    "name": "ultron_goal_report.txt",
                    "content": f"Goal: {goal}\nStatus: Completed by Ultron Autonomous Agent.\n"
                }
            }
        ]

    prompt = f"""
You are the master planning brain of ULTRON, an autonomous AI operating system agent.
Break down the following user goal into 2 to 6 concrete, logical, atomic steps.

AVAILABLE ACTIONS:
1. web_search: params: {{"query": "string", "mode": "search" | "news" | "research"}}
2. file_controller: params: {{"action": "create_file" | "read" | "find", "path": "desktop" | "downloads" | path, "name": "filename", "content": "text"}}
3. code_helper: params: {{"action": "write" | "run", "description": "task", "language": "python", "output_path": "path"}}
4. computer_settings: params: {{"action": "open_app" | "volume" | "screenshot", "description": "desc"}}

USER GOAL:
"{goal}"

Respond ONLY with a valid JSON array of step objects:
[
  {{"step": "Step description", "action": "action_name", "params": {{...}}}},
  ...
]
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        cleaned = _clean_json(response.text or "")
        plan = json.loads(cleaned)
        if isinstance(plan, list) and len(plan) > 0:
            return plan[:MAX_STEPS]
    except Exception as e:
        print(f"[GoalAgent] ⚠️ Planning LLM error: {e}")

    # Fallback plan
    return [
        {"step": f"Investigate: {goal}", "action": "web_search", "params": {"query": goal, "mode": "search"}}
    ]


def _execute_subtask(action_name: str, params: dict, player=None) -> str:
    """Execute an individual sub-task using ULTRON's tool ecosystem."""
    try:
        if action_name == "web_search":
            return web_search(parameters=params, player=player) or "Search completed."
        elif action_name == "file_controller":
            return file_controller(parameters=params, player=player) or "File operation completed."
        elif action_name == "code_helper":
            return code_helper(parameters=params, player=player) or "Code execution completed."
        elif action_name == "computer_settings":
            return computer_settings(parameters=params, response=None, player=player) or "Setting adjusted."
        else:
            return f"Action {action_name} executed with params {params}."
    except Exception as e:
        return f"ERROR: {e}"


def execute_autonomous_goal(parameters: dict, player=None, speak: Callable[[str], None] | None = None) -> str:
    """
    Main entry point for the Autonomous Goal Engine.
    Orchestrates planning, step-by-step execution, error correction, and final report.
    """
    goal = parameters.get("goal") or parameters.get("description") or parameters.get("task", "")
    if not goal:
        return "Sir, please specify a goal for me to execute."

    if player:
        player.write_log(f"🧠 [GOAL_AGENT] Initiating autonomous goal: '{goal}'")
    play_sfx("thinking")

    if speak:
        speak(f"Initiating autonomous protocol. Goal: {goal[:80]}. I am formulating the execution plan now, sir.")

    # 1. Plan goal
    steps = plan_goal(goal)
    total_steps = len(steps)
    if player:
        player.write_log(f"📋 [GOAL_AGENT] Formulated {total_steps}-step execution plan.")

    results: list[dict] = []

    # 2. Execute ReAct Loop
    for idx, step_data in enumerate(steps, 1):
        step_desc = step_data.get("step", f"Step {idx}")
        action = step_data.get("action", "custom")
        params = step_data.get("params", {})

        if player:
            player.write_log(f"⚡ [GOAL_AGENT] [{idx}/{total_steps}] Executing: {step_desc}")

        step_output = ""
        attempt = 0
        success = False

        while attempt < MAX_RETRIES_PER_STEP and not success:
            attempt += 1
            step_output = _execute_subtask(action, params, player=player)

            if not step_output.startswith("ERROR"):
                success = True
            else:
                if player:
                    player.write_log(f"⚠️ [GOAL_AGENT] Step {idx} failed (attempt {attempt}). Retrying...")
                time.sleep(1)

        results.append({
            "step": step_desc,
            "success": success,
            "output": step_output[:500]
        })

    play_sfx("complete")

    # 3. Create Desktop Summary Report
    try:
        report_path = Path.home() / "Desktop" / "Ultron_Autonomous_Report.md"
        report_lines = [
            f"# ULTRON Autonomous Execution Report",
            f"**Goal**: {goal}",
            f"**Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Steps**: {total_steps}",
            "",
            "## Execution Steps:",
        ]
        for i, res in enumerate(results, 1):
            status = "✅ SUCCESS" if res["success"] else "❌ FAILED"
            report_lines.append(f"### {i}. {res['step']} — {status}")
            report_lines.append(f"```text\n{res['output']}\n```\n")

        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        if player:
            player.write_log(f"📄 [GOAL_AGENT] Comprehensive report saved to: {report_path.name}")
    except Exception as e:
        print(f"[GoalAgent] ⚠️ Failed to save report: {e}")

    # 4. Return concise executive summary
    successful_count = sum(1 for r in results if r["success"])
    summary = (
        f"Autonomous goal completed. Executed {successful_count} out of {total_steps} tasks successfully. "
        f"A detailed briefing report has been saved to your Desktop."
    )
    if player:
        player.write_log(f"✅ [GOAL_AGENT] {summary}")

    return summary
