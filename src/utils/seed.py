"""Deterministic seed helpers."""

from __future__ import annotations

import os
import random


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy, and hash randomization where possible."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    try:
        import numpy as np
    except ImportError:
        return
    np.random.seed(seed)

