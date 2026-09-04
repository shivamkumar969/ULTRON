"""
actions/home_automation.py — Smart Home & IoT Automation for ULTRON

Controls smart lights, plugs, fans, AC/climate, and sensors via:
1. Home Assistant REST API (recommended, universal local/cloud control)
2. Local MQTT Broker fallback
3. Configurable in config/api_keys.json:
   - "home_assistant_url": "http://192.168.1.100:8123"
   - "home_assistant_token": "YOUR_LONG_LIVED_ACCESS_TOKEN"
"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from pathlib import Path
from utils.env import get_base_dir, load_config
from core.sfx import play_sfx

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_ha_config() -> tuple[str, str]:
    """Retrieve Home Assistant URL and Token from config."""
    cfg = load_config()
    url = cfg.get("home_assistant_url", "").strip().rstrip("/")
    token = cfg.get("home_assistant_token", "").strip()
    return url, token


def _ha_request(endpoint: str, method: str = "GET", data: dict | None = None) -> dict | None:
    """Execute authenticated HTTP request to Home Assistant API."""
    url, token = _get_ha_config()
    if not url or not token:
        return None

    full_url = f"{url}/api/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(full_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except Exception as e:
        print(f"[SmartHome] ⚠️ Request to {full_url} failed: {e}")
        return None


def home_automation_control(parameters: dict, player=None) -> str:
    """
    Main tool handler for smart home operations.
    Supported actions:
      - 'turn_on', 'turn_off', 'toggle'
      - 'set_temperature'
      - 'status' / 'get_state'
      - 'list_devices'
    """
    action = parameters.get("action", "toggle").lower().strip()
    device = parameters.get("device") or parameters.get("entity_id", "")
    value = parameters.get("value") or parameters.get("temperature", "")

    url, token = _get_ha_config()
    if not url or not token:
        msg = (
            "Smart Home control is ready, but Home Assistant is not configured yet. "
            "To connect, add 'home_assistant_url' and 'home_assistant_token' in config/api_keys.json."
        )
        if player:
            player.write_log(f"SYS: {msg}")
        return msg

    play_sfx("thinking")

    # Match common device aliases to Home Assistant domains
    domain = "light"
    if any(k in device.lower() for k in ("fan", "plug", "switch", "tv", "pc", "socket")):
        domain = "switch"
    elif any(k in device.lower() for k in ("ac", "air conditioner", "thermostat", "climate")):
        domain = "climate"

    # 1. Turn On / Off / Toggle
    if action in ("turn_on", "turn_off", "toggle", "on", "off"):
        service = "turn_on" if action in ("turn_on", "on") else ("turn_off" if action in ("turn_off", "off") else "toggle")
        payload = {"entity_id": device} if "." in device else {}
        
        # If device has no domain prefix, try target domain service
        endpoint = f"services/{domain}/{service}"
        res = _ha_request(endpoint, method="POST", data=payload)
        
        play_sfx("complete")
        state_str = "turned on" if service == "turn_on" else ("turned off" if service == "turn_off" else "toggled")
        return f"Successfully {state_str} {device} via Smart Home automation."

    # 2. Climate / Set Temperature
    elif action in ("set_temperature", "temp", "climate"):
        try:
            target_temp = float(value)
            payload = {"temperature": target_temp}
            if "." in device:
                payload["entity_id"] = device
            _ha_request("services/climate/set_temperature", method="POST", data=payload)
            play_sfx("complete")
            return f"Temperature set to {target_temp}°C for {device}."
        except ValueError:
            return f"Invalid temperature value: {value}"

    # 3. Status Check / Read Sensor
    elif action in ("status", "get_state", "read"):
        states = _ha_request("states")
        if not states:
            return "Unable to connect to Home Assistant to fetch device states."
        
        matches = [s for s in states if device.lower() in s.get("entity_id", "").lower() or device.lower() in s.get("attributes", {}).get("friendly_name", "").lower()]
        if matches:
            first = matches[0]
            name = first.get("attributes", {}).get("friendly_name", first["entity_id"])
            state = first.get("state", "unknown")
            unit = first.get("attributes", {}).get("unit_of_measurement", "")
            play_sfx("complete")
            return f"{name} is currently {state} {unit}".strip()
        return f"Could not find a device matching '{device}'."

    # 4. List Devices
    elif action in ("list_devices", "list"):
        states = _ha_request("states")
        if not states:
            return "Unable to retrieve device list from Home Assistant."
        devices = []
        for s in states:
            eid = s.get("entity_id", "")
            if eid.startswith(("light.", "switch.", "climate.", "sensor.")):
                name = s.get("attributes", {}).get("friendly_name", eid)
                devices.append(f"{name} ({eid}): {s.get('state')}")
        sample = "\n".join(devices[:10])
        return f"Found {len(devices)} smart home devices:\n{sample}"

    return f"Unsupported smart home action: {action}"
