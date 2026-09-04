"""
actions/email_calendar.py — Email & Calendar Automation for ULTRON

Automates email and schedule management via:
1. Native Windows Outlook Desktop (win32com — no passwords needed if Outlook is installed)
2. Universal IMAP/SMTP fallback (configurable in config/api_keys.json)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional
from utils.env import get_base_dir, load_config
from core.sfx import play_sfx

_HAS_WIN32 = False
try:
    import win32com.client
    _HAS_WIN32 = True
except ImportError:
    pass


def _get_outlook():
    """Attempt to connect to native Microsoft Outlook Application."""
    if not _HAS_WIN32:
        return None
    try:
        return win32com.client.Dispatch("Outlook.Application")
    except Exception:
        return None


def read_unread_emails(count: int = 5, player=None) -> str:
    """Read the latest unread emails from the Inbox."""
    outlook = _get_outlook()
    if outlook:
        try:
            mapi = outlook.GetNamespace("MAPI")
            inbox = mapi.GetDefaultFolder(6)  # 6 = olFolderInbox
            messages = inbox.Items.Restrict("[UnRead] = True")
            messages.Sort("[ReceivedTime]", True)

            results = []
            for i, msg in enumerate(messages):
                if i >= count:
                    break
                try:
                    sender = getattr(msg, "SenderName", "Unknown")
                    subject = getattr(msg, "Subject", "(No Subject)")
                    received = getattr(msg, "ReceivedTime", "")
                    time_str = received.strftime("%I:%M %p") if hasattr(received, "strftime") else str(received)
                    results.append(f"• From {sender}: \"{subject}\" at {time_str}")
                except Exception:
                    continue

            play_sfx("complete")
            if not results:
                return "Sir, you have no unread emails in your Outlook inbox."

            summary = f"You have {len(results)} unread emails:\n" + "\n".join(results)
            if player:
                player.write_log(f"📧 {summary}")
            return summary
        except Exception as e:
            print(f"[Email] ⚠️ Outlook read error: {e}")

    # Fallback to IMAP if configured
    cfg = load_config()
    email_user = cfg.get("email_address")
    email_pass = cfg.get("email_password")
    imap_server = cfg.get("imap_server", "imap.gmail.com")

    if email_user and email_pass:
        import imaplib
        import email
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.select("inbox")
            _, data = mail.search(None, "UNSEEN")
            ids = data[0].split()
            recent_ids = ids[-count:]
            recent_ids.reverse()

            results = []
            for num in recent_ids:
                _, msg_data = mail.fetch(num, "(RFC822.HEADER)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg.get("Subject", "(No Subject)")
                        sender = msg.get("From", "Unknown")
                        results.append(f"• From {sender}: \"{subject}\"")
            mail.close()
            mail.logout()
            play_sfx("complete")
            return f"You have {len(results)} unread emails:\n" + "\n".join(results) if results else "No unread emails found."
        except Exception as e:
            return f"IMAP connection failed: {e}"

    return (
        "Email integration is available. To enable, open Microsoft Outlook Desktop, "
        "or configure 'email_address' and 'email_password' in config/api_keys.json."
    )


def send_email(recipient: str, subject: str, body: str, player=None) -> str:
    """Send an email to a recipient."""
    outlook = _get_outlook()
    if outlook:
        try:
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = recipient
            mail.Subject = subject
            mail.Body = body
            mail.Send()
            play_sfx("complete")
            msg = f"Email successfully dispatched to {recipient} with subject: '{subject}'."
            if player:
                player.write_log(f"📧 {msg}")
            return msg
        except Exception as e:
            print(f"[Email] ⚠️ Outlook send error: {e}")

    # SMTP fallback
    cfg = load_config()
    email_user = cfg.get("email_address")
    email_pass = cfg.get("email_password")
    smtp_server = cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = cfg.get("smtp_port", 587)

    if email_user and email_pass:
        import smtplib
        from email.mime.text import MIMEText
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = email_user
            msg["To"] = recipient

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(email_user, [recipient], msg.as_string())
            play_sfx("complete")
            return f"Email successfully sent to {recipient}."
        except Exception as e:
            return f"SMTP send failed: {e}"

    return "No email client or credentials configured to send emails."


def create_calendar_event(title: str, start_time: str, duration_minutes: int = 30, description: str = "", player=None) -> str:
    """Create a new calendar appointment in Outlook."""
    outlook = _get_outlook()
    if not outlook:
        return "Calendar automation requires Microsoft Outlook Desktop on Windows."

    try:
        appt = outlook.CreateItem(1)  # 1 = olAppointmentItem
        appt.Subject = title
        appt.Body = description
        appt.Duration = duration_minutes

        # Try parsing start_time (ISO or natural format)
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            appt.Start = dt.strftime("%m/%d/%Y %I:%M %p")
        except Exception:
            # Assume start_time is already formatted or relative
            appt.Start = start_time

        appt.ReminderSet = True
        appt.ReminderMinutesBeforeStart = 15
        appt.Save()

        play_sfx("complete")
        msg = f"Calendar appointment '{title}' scheduled for {appt.Start} ({duration_minutes} min)."
        if player:
            player.write_log(f"📅 {msg}")
        return msg
    except Exception as e:
        return f"Failed to schedule calendar event: {e}"


def email_calendar_action(parameters: dict, player=None) -> str:
    """Unified tool dispatch for email and calendar."""
    action = parameters.get("action", "read").lower().strip()

    if action in ("read", "unread", "check_inbox", "inbox"):
        count = int(parameters.get("count", 5))
        return read_unread_emails(count=count, player=player)

    elif action in ("send", "compose", "send_email"):
        recipient = parameters.get("recipient") or parameters.get("to", "")
        subject = parameters.get("subject", "Message from Ultron")
        body = parameters.get("body") or parameters.get("content", "")
        if not recipient:
            return "Please provide a recipient email address."
        return send_email(recipient=recipient, subject=subject, body=body, player=player)

    elif action in ("calendar", "schedule", "event", "appointment"):
        title = parameters.get("title") or parameters.get("event", "Meeting")
        start = parameters.get("start_time") or parameters.get("time", "")
        duration = int(parameters.get("duration", 30))
        desc = parameters.get("description", "")
        return create_calendar_event(title=title, start_time=start, duration_minutes=duration, description=desc, player=player)

    return f"Unsupported email/calendar action: {action}"
