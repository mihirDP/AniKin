import os
import shutil
import urllib.request
import re

# Define paths
SPARE_DIR = r"D:\Coding_Projects\AniKin Spare\AniKinIconsPack"
DEST_DIR = r"D:\Coding_Projects\AniKin\AniKin\scripts\anikin\icons"

# 1. Rename and Copy Mappings
COPY_MAPPINGS = {
    "AlignRotationsOnly.svg": "align_rotate.svg",
    "AlignSelectedToLast.svg": "align_all.svg",
    "AlignTranslationsOnly.svg": "align_translate.svg",
    "AniCleanup.svg": "cleanup.svg",
    "AniGround.svg": "ground.svg",
    "AutoTangent.svg": "auto.svg",
    "CopyPose.svg": "copy_pose.svg",
    "DuplicateKey.svg": "duplicate.svg",
    "FlatCurve.svg": "flat.svg",
    "LinearCurve.svg": "linear.svg",
    "LockChannels.svg": "lock.svg",
    "MirrorPose.svg": "mirror_pose.svg",
    "PastePose.svg": "paste_pose.svg",
    "ResetPoseIco.svg": "reset.svg",
    "SetKey.svg": "key.svg",
    "SmartKey.svg": "smart_key.svg",
    "SplineTangent.svg": "spline.svg",
    "StaggerKeys.svg": "offset.svg",
    "SteppedCurve.svg": "step.svg",
    "UnlockChannels.svg": "unlock.svg",
}

# Colors for the 5 families
ORANGE = "#f97316"
BLUE = "#3b82f6"
PURPLE = "#a855f7"
GREEN = "#10b981"
RED = "#ef4444"

# 2. File to Color Mapping
COLOR_MAP = {
    # Core Animation (Orange)
    "reset.svg": ORANGE,
    "align_all.svg": ORANGE,
    "align_translate.svg": ORANGE,
    "align_rotate.svg": ORANGE,
    "ground.svg": ORANGE,
    "nudge_left.svg": ORANGE,
    "nudge_right.svg": ORANGE,
    "nudge_left_fast.svg": ORANGE,
    "nudge_right_fast.svg": ORANGE,
    "offset.svg": ORANGE,
    "duplicate.svg": ORANGE,
    "smart_key.svg": ORANGE,
    "wand.svg": ORANGE,
    "auto.svg": ORANGE,
    "flat.svg": ORANGE,
    "linear.svg": ORANGE,
    "step.svg": ORANGE,
    "spline.svg": ORANGE,
    "key.svg": ORANGE,
    "delkey.svg": ORANGE,
    "tween.svg": ORANGE,
    "smooth.svg": ORANGE,
    "euler.svg": ORANGE,
    "cleanup.svg": ORANGE,
    "wave_sine.svg": ORANGE,
    "activity.svg": ORANGE,
    "play_pause.svg": ORANGE,
    "first_key.svg": ORANGE,
    "prev_key.svg": ORANGE,
    "next_key.svg": ORANGE,
    "last_key.svg": ORANGE,
    "copy_pose.svg": ORANGE,
    "paste_pose.svg": ORANGE,
    "lock.svg": ORANGE,
    "unlock.svg": ORANGE,

    # Workflow (Blue)
    "bake_to_locator.svg": BLUE,
    "bake_from_locator.svg": BLUE,
    "selection_sets.svg": BLUE,
    "bookmark.svg": BLUE,
    "camera.svg": BLUE,
    "settings.svg": BLUE,
    "hotkeys.svg": BLUE,

    # Visual (Purple)
    "trail.svg": PURPLE,
    "ghost.svg": PURPLE,

    # Kinematics (Green)
    "mirror_pose.svg": GREEN,

    # Pipeline (Red)
    "stethoscope.svg": RED,
    "file_export.svg": RED,
}

def download_missing_icons():
    # We want file_export.svg from Lucide static package
    url = "https://unpkg.com/lucide-static@0.344.0/icons/file-output.svg"
    dest = os.path.join(DEST_DIR, "file_export.svg")
    print(f"Downloading {url} to {dest}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print("Download successful!")
    except Exception as e:
        print(f"Failed to download file_export.svg: {e}")

def copy_spare_icons():
    if not os.path.exists(SPARE_DIR):
        print(f"Spare icons directory not found: {SPARE_DIR}")
        return
    for src_name, dest_name in COPY_MAPPINGS.items():
        src_path = os.path.join(SPARE_DIR, src_name)
        dest_path = os.path.join(DEST_DIR, dest_name)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            print(f"Copied {src_name} -> {dest_name}")
        else:
            print(f"Warning: Source file {src_path} not found.")

def recolor_all_icons():
    for filename in os.listdir(DEST_DIR):
        if not filename.endswith(".svg"):
            continue
        filepath = os.path.join(DEST_DIR, filename)
        color = COLOR_MAP.get(filename, "#ffffff") # default to white if not in map
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Perform color replacements
        # Match stroke="#000", stroke='#000', stroke="currentColor", stroke='#000000', etc.
        new_content = re.sub(r'stroke\s*=\s*["\'](currentColor|#[0-9a-fA-F]{3,6})["\']', f'stroke="{color}"', content)
        # Match fill="currentColor"
        new_content = re.sub(r'fill\s*=\s*["\'](currentColor)["\']', f'fill="{color}"', new_content)
        # Match CSS rules like stroke: #000; or stroke:#000000; or stroke:currentColor;
        new_content = re.sub(r'stroke\s*:\s*(currentColor|#[0-9a-fA-F]{3,6}|black)\s*;?', f'stroke: {color};', new_content)
        # Match CSS rules like fill: currentColor;
        new_content = re.sub(r'fill\s*:\s*(currentColor)\s*;?', f'fill: {color};', new_content)

        # Let's check if the file didn't change (e.g. if stroke was something else, like #000 in lowercase without hex)
        # We can also do a direct replacement of stroke: #000 to cover class styles
        new_content = new_content.replace('stroke: #000', f'stroke: {color}')

        # Save back
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Recolored {filename} to {color}")

if __name__ == "__main__":
    copy_spare_icons()
    download_missing_icons()
    recolor_all_icons()
    print("All tasks completed successfully!")
