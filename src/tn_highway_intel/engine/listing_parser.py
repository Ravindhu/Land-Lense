"""Extract land-listing fields from a broker message (Phase 6, rule-based, no model call).

Only the fields in PropertyPin are returned. The phone number is masked before it leaves this module:
the full number is never stored (docs/SECURITY_AND_LEGAL.md section 2).
Patterns cover English and common Tamil labels. Anything not found is None.
"""

from __future__ import annotations

import re
from typing import Optional

LAKH = 100_000
CRORE = 10_000_000

VILLAGE_RE = re.compile(r"(?:village|ஊர்|கிராமம்)\s*[:\-]?\s*([^\n,;]{2,60})", re.IGNORECASE)
SURVEY_RE = re.compile(r"(?:survey\s*(?:no\.?|number)?|sur\.?\s*no\.?|சர்வே\s*(?:எண்)?)\s*[:\-]?\s*([0-9]{1,4}(?:[/\-][0-9A-Za-z]{1,4})*)", re.IGNORECASE)
PRICE_RE = re.compile(r"(?:price|rate|விலை)\s*[:\-]?\s*(?:rs\.?|₹|inr)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(lakh|lac|crore|cr)?", re.IGNORECASE)
SIZE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(cents?|sq\.?\s*ft|sqft|acres?)", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?91[\s-]?)?([6-9][0-9]{9})")


def mask_phone(number: str) -> str:
    digits = re.sub(r"\D", "", number)
    return "x" * (len(digits) - 4) + digits[-4:]


def _price_inr(amount: str, unit: Optional[str]) -> Optional[int]:
    try:
        value = float(amount.replace(",", ""))
    except ValueError:
        return None
    multiplier = 1
    if unit:
        u = unit.lower()
        multiplier = LAKH if u in ("lakh", "lac") else CRORE
    return int(round(value * multiplier))


def parse_listing(text: str) -> dict[str, Optional[object]]:
    village = VILLAGE_RE.search(text)
    survey = SURVEY_RE.search(text)
    price = PRICE_RE.search(text)
    size = SIZE_RE.search(text)
    phone = PHONE_RE.search(text)
    return {
        "village": village.group(1).strip() if village else None,
        "survey_ref": survey.group(1).strip() if survey else None,
        "price_inr": _price_inr(price.group(1), price.group(2)) if price else None,
        "plot_size": f"{size.group(1)} {size.group(2)}" if size else None,
        "contact_phone": mask_phone(phone.group(1)) if phone else None,
    }
