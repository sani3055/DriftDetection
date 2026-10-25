from __future__ import annotations

import random

import numpy as np

from src.utils.config import load_yaml, project_path
from src.utils.seed import seed_everything


def test_base_config_loads() -> None:
    config = load_yaml("configs/base.yaml")
    assert config["project"]["python_version"] == "3.11"
    assert config["random"]["seed"] == 42


def test_project_path_handles_relative_and_absolute_paths() -> None:
    assert project_path("D:/project", "data/file.csv").as_posix().endswith("project/data/file.csv")
    assert project_path("D:/project", "D:/data/file.csv").as_posix() == "D:/data/file.csv"


def test_seed_everything_is_repeatable() -> None:
    seed_everything(123)
    first = (random.random(), float(np.random.random()))
    seed_everything(123)
    second = (random.random(), float(np.random.random()))
    assert first == second

