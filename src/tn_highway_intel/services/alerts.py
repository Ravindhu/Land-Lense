"""Telegram alerts with redaction (Phase 7, docs/API.md section 2, docs/SECURITY_AND_LEGAL.md section 2).

Every alert passes through redact() before it is sent:
- PAN-shaped and Aadhaar-shaped numbers are removed.
- Phone numbers are masked to their last four digits.
- If the text contains a protected term (for example an owner name passed in by the caller),
  the alert is refused and nothing is sent.
Failed sends are queued on disk and retried by flush_pending().
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Optional

import requests

TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT_S = 10

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_RE = re.compile(r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b")
PHONE_RE = re.compile(r"(?:\+?91[\s-]?)?([6-9][0-9]{9})\b")


class AlertRefused(ValueError):
    """Raised when an alert would carry a protected term. The alert is not sent."""


def redact(text: str) -> str:
    text = PAN_RE.sub("[id removed]", text)
    text = AADHAAR_RE.sub("[id removed]", text)
    text = PHONE_RE.sub(lambda m: "x" * 6 + m.group(1)[-4:], text)
    return text


def refuse_if_protected(text: str, protected_terms: Iterable[str]) -> None:
    lowered = text.lower()
    for term in protected_terms:
        if term and term.strip() and term.strip().lower() in lowered:
            raise AlertRefused("alert contains a protected term and was not sent")


def send_alert(
    text: str,
    *,
    token: Optional[str],
    chat_id: Optional[str],
    protected_terms: Iterable[str] = (),
    pending_path: Optional[Path] = None,
    session=requests,
) -> bool:
    """Send one alert. Returns True when Telegram accepted it. Queues on failure."""
    clean = redact(text)
    refuse_if_protected(clean, protected_terms)
    if not token or not chat_id:
        if pending_path is not None:
            _queue(pending_path, clean)
        return False
    try:
        response = session.post(
            TELEGRAM_URL.format(token=token),
            data={"chat_id": chat_id, "text": clean, "disable_web_page_preview": True},
            timeout=TIMEOUT_S,
        )
        ok = response.status_code == 200
    except Exception:  # network or TLS failure; the token is never printed
        ok = False
    if not ok and pending_path is not None:
        _queue(pending_path, clean)
    return ok


def _queue(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")


def flush_pending(pending_path: Path, *, token: str, chat_id: str, session=requests) -> int:
    if not pending_path.exists():
        return 0
    lines = [json.loads(line) for line in pending_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    remaining = []
    sent = 0
    for item in lines:
        if send_alert(item["text"], token=token, chat_id=chat_id, session=session):
            sent += 1
        else:
            remaining.append(item)
    if remaining:
        pending_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in remaining) + "\n", encoding="utf-8")
    else:
        pending_path.unlink()
    return sent
