"""Load config/settings.yaml and .env from the project root (Phase 0)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from tn_highway_intel.domain.models import Stage

MARGIN_FT_TO_M = 0.3048


class MissingSecret(RuntimeError):
    """Raised when a required environment variable is unset. The value is never printed."""


class _Cfg(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TargetZoneSettings(_Cfg):
    default_row_width_m: Optional[float] = Field(default=None, gt=0)
    margin_ft: float = Field(default=20, ge=0)
    sides: Literal["both"] = "both"

    @property
    def margin_m(self) -> float:
        return round(self.margin_ft * MARGIN_FT_TO_M, 3)


class CollectorSettings(_Cfg):
    enabled: bool = False
    terms_cleared: bool = False
    min_interval_s: float = Field(default=5, ge=0)


class OcrSettings(_Cfg):
    engine: Literal["gemini", "tesseract"] = "gemini"
    model: str = "gemini-2.5-flash"
    prompt_version: str = "v1"
    timeout_s: float = Field(default=120, gt=0)


class Settings(_Cfg):
    crs: str = "EPSG:32643"
    approval_stage: Stage = "3D"
    target_zone: TargetZoneSettings = Field(default_factory=TargetZoneSettings)
    snap_tolerance_m: float = Field(default=50, ge=0)
    ocr: OcrSettings = Field(default_factory=OcrSettings)
    llm_monthly_budget_usd: float = Field(default=0, ge=0)
    llm_alert_fraction: float = Field(default=0.8, gt=0, le=1)
    collectors: dict[str, CollectorSettings] = Field(default_factory=dict)

    def collector(self, name: str) -> CollectorSettings:
        """Return a collector's settings; unknown collectors are disabled."""
        return self.collectors.get(name, CollectorSettings())


def project_root(start: Optional[Path] = None) -> Path:
    """Find the project root: TN_INTEL_ROOT if set, else the nearest parent with pyproject.toml."""
    override = os.environ.get("TN_INTEL_ROOT")
    if override:
        return Path(override).resolve()
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("project root (pyproject.toml) not found")


def load_env(root: Optional[Path] = None) -> None:
    """Load .env from the project root if present. Existing environment variables win."""
    env_file = (root or project_root()) / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_settings(path: Optional[Path] = None) -> Settings:
    root = project_root()
    cfg_path = path or root / "config" / "settings.yaml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return Settings.model_validate(data)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingSecret(f"{name} is not set")
    return value


def get_env(name: str) -> Optional[str]:
    value = os.environ.get(name, "").strip()
    return value or None
