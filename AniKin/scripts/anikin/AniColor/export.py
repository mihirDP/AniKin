"""
AniColor — export.py
JSON/CSV export and import of label data, plus template loading.
"""

import os
import json
import csv
import maya.cmds as cmds
from anikin.core.log import log_debug
from anikin.AniColor.core import (
    load_payload, save_payload, rebuild_from_payload,
)

# Templates directory
_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def export_json(file_path):
    """Export all AniColor data as JSON."""
    data = load_payload()
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        cmds.inViewMessage(
            amg="<hl>AniColor</hl>: Exported to JSON",
            pos="topCenter", fade=True, fadeStayTime=1500)
        return True
    except Exception as e:
        cmds.warning("AniColor: Export failed: {}".format(e))
        return False


def import_json(file_path, merge=True):
    """
    Import AniColor data from a JSON file.
    If merge=True, non-conflicting entries are added to existing data.
    If merge=False, existing data is replaced entirely.
    """
    if not os.path.exists(file_path):
        cmds.warning("AniColor: File not found: {}".format(file_path))
        return False
    try:
        with open(file_path, "r") as f:
            imported = json.load(f)

        if not isinstance(imported, dict):
            cmds.warning("AniColor: Invalid JSON format.")
            return False

        if merge:
            current = load_payload()
            # Merge palettes (add new ones that don't conflict by ID)
            existing_ids = {p["id"] for p in current.get("palettes", [])}
            for p in imported.get("palettes", []):
                if p["id"] not in existing_ids:
                    current.setdefault("palettes", []).append(p)
            # Merge frames (don't overwrite existing)
            for frame_str, entry in imported.get("frames", {}).items():
                if frame_str not in current.get("frames", {}):
                    current.setdefault("frames", {})[frame_str] = entry
            # Merge ranges
            for rid, rng in imported.get("ranges", {}).items():
                if rid not in current.get("ranges", {}):
                    current.setdefault("ranges", {})[rid] = rng
            save_payload(current)
        else:
            save_payload(imported)

        rebuild_from_payload()
        cmds.inViewMessage(
            amg="<hl>AniColor</hl>: Imported labels from JSON",
            pos="topCenter", fade=True, fadeStayTime=1500)
        return True
    except Exception as e:
        cmds.warning("AniColor: Import failed: {}".format(e))
        return False


def export_csv(file_path):
    """Export frame labels as CSV."""
    data = load_payload()
    palette_map = {p["id"]: p["name"] for p in data.get("palettes", [])}
    try:
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Frame", "Palette", "Label", "Notes"])
            for frame_str in sorted(data.get("frames", {}).keys(), key=int):
                entry = data["frames"][frame_str]
                writer.writerow([
                    frame_str,
                    palette_map.get(entry.get("palette_id", ""), ""),
                    entry.get("label", ""),
                    entry.get("notes", ""),
                ])
        cmds.inViewMessage(
            amg="<hl>AniColor</hl>: Exported to CSV",
            pos="topCenter", fade=True, fadeStayTime=1500)
        return True
    except Exception as e:
        cmds.warning("AniColor: CSV export failed: {}".format(e))
        return False


def list_templates():
    """Return a list of available template names."""
    if not os.path.isdir(_TEMPLATES_DIR):
        return []
    templates = []
    for f in sorted(os.listdir(_TEMPLATES_DIR)):
        if f.endswith(".json"):
            templates.append(os.path.splitext(f)[0])
    return templates


def load_template(template_name):
    """Load a palette template, replacing the current palette slots."""
    path = os.path.join(_TEMPLATES_DIR, template_name + ".json")
    if not os.path.exists(path):
        cmds.warning("AniColor: Template '{}' not found.".format(template_name))
        return False
    return import_json(path, merge=False)
