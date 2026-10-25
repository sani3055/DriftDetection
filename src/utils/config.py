"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping and reject non-mapping roots."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Configuration root must be a mapping: {config_path}")
    return loaded


def project_path(project_root: str | Path, configured_path: str | Path) -> Path:
    """Resolve a configured path without changing the user's source data."""
    path = Path(configured_path)
    if path.is_absolute():
        return path
    return Path(project_root) / path

