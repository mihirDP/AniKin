import os
import shutil

base_dir = r"d:\Coding_Projects\AniKin\AniKin\scripts\anikin"
tools_dir = os.path.join(base_dir, "tools")

module_map = {
    "tween.py": "AniTween",
    "anim_offset.py": "AniOffset",
    "smart_bake.py": "AniBake",
    "pose.py": "AniMirror", # Pose contains copy/paste/mirror
    "ghosting.py": "AniGhost",
    "motion_trail.py": "AniMotion",
    "align.py": "AniAlign",
    "channels.py": "AniChannels",
    "hotkeys.py": "AniHotkeys",
    "key_nav.py": "AniKeyNav",
    "nudge.py": "AniNudge",
    "selection_sets.py": "AniSets",
    "smooth.py": "AniSmooth",
    "tangents.py": "AniTangents"
}

# 1. Create module directories and move files
for old_file, new_mod in module_map.items():
    old_path = os.path.join(tools_dir, old_file)
    if os.path.exists(old_path):
        new_mod_dir = os.path.join(base_dir, new_mod)
        os.makedirs(new_mod_dir, exist_ok=True)
        new_path = os.path.join(new_mod_dir, "core.py")
        shutil.move(old_path, new_path)
        
        # Create __init__.py mapping the functions
        with open(os.path.join(new_mod_dir, "__init__.py"), "w", encoding="utf-8") as f:
            f.write(f"from .core import *\n")

# 2. Update imports in all python files
import glob

all_py_files = glob.glob(os.path.join(base_dir, "**", "*.py"), recursive=True)
all_py_files.extend(glob.glob(os.path.join(r"d:\Coding_Projects\AniKin\AniKin\tests", "*.py")))

for py_file in all_py_files:
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    for old_file, new_mod in module_map.items():
        old_mod_name = old_file.replace(".py", "")
        # Replace absolute imports
        content = content.replace(f"anikin.tools import {old_mod_name}", f"anikin import {new_mod}")
        content = content.replace(f"anikin.tools.{old_mod_name}", f"anikin.{new_mod}")
        # Replace method calls
        content = content.replace(f"{old_mod_name}.", f"{new_mod}.")
        
    if content != original_content:
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(content)

print("Refactoring complete.")
