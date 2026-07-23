"""
json_io.py — Safe JSON file reader/writer for AniPose Pro V3.1.
"""

import os
import json


def safe_read_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def safe_write_json(filepath: str, data: dict, indent: int = 4) -> bool:
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    try:
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(tmp_path, filepath)
        return True
    except Exception:
        return False
