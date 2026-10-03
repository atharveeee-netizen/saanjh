"""Configuration loading.

Configuration is loaded per run (not at import time) so tests and sensitivity runs can
override any value without editing config/saanjh.yaml.
"""
import copy
import os

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(REPO_ROOT, "config", "saanjh.yaml")


def deep_update(base, overrides):
    """Recursively merge ``overrides`` into a copy of ``base``."""
    out = copy.deepcopy(base)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_update(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(overrides=None, path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return deep_update(cfg, overrides)


def repo_path(*parts):
    return os.path.join(REPO_ROOT, *parts)
