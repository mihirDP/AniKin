import os

# Define the color mapping for our tool categories
# Colors inspired by modern dark theme UI and AnimBot's color-coded functional groups
CATEGORY_COLORS = {
    # TRANSFORM (Purple)
    "align_all.svg": "#c678dd",
    "align_translate.svg": "#c678dd",
    "align_rotate.svg": "#c678dd",
    
    # TIMING / STAGGER (Green)
    "nudge_left.svg": "#98c379",
    "nudge_right.svg": "#98c379",
    "nudge_left_fast.svg": "#98c379",
    "nudge_right_fast.svg": "#98c379",
    "anim_offset.svg": "#98c379", # If we have one
    
    # TANGENTS (Orange)
    "auto.svg": "#d19a66",
    "flat.svg": "#d19a66",
    "linear.svg": "#d19a66",
    "step.svg": "#d19a66",
    "spline.svg": "#d19a66",
    
    # VISUALIZATION (Teal/Cyan)
    "trail.svg": "#56b6c2",
    "ghost.svg": "#56b6c2",
    
    # CHANNELS (Pink/Red)
    "lock.svg": "#e06c75",
    "unlock.svg": "#e06c75",
    "key.svg": "#e06c75",
    "delkey.svg": "#e06c75",
    
    # TWEENS / FILTERS (Yellow)
    "euler.svg": "#e5c07b",
    "smooth.svg": "#e5c07b",
    
    # WORKFLOW / SETUP (Light Blue/Grey)
    "bake_to_locator.svg": "#61afef",
    "bake_from_locator.svg": "#61afef",
    "selection_sets.svg": "#61afef",
    "settings.svg": "#abb2bf",
    "hotkeys.svg": "#abb2bf",
}

def recolor_svgs(icons_dir):
    for filename in os.listdir(icons_dir):
        if not filename.endswith(".svg"):
            continue
            
        filepath = os.path.join(icons_dir, filename)
        
        # Determine the color for this specific icon
        color = CATEGORY_COLORS.get(filename, "#ffffff") # Default to white if not found
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Lucide uses stroke="currentColor". We'll replace it with the hex color.
        # It also has stroke-width="2", we can make it slightly thicker for better visibility in Maya
        new_content = content.replace('stroke="currentColor"', f'stroke="{color}"')
        new_content = new_content.replace('stroke-width="2"', 'stroke-width="2.5"')
        
        with open(filepath, 'w') as f:
            f.write(new_content)
            
        print(f"Recolored {filename} to {color}")

if __name__ == "__main__":
    icons_dir = r"d:\Coding_Projects\AniKin\AniKin\scripts\anikin\icons"
    recolor_svgs(icons_dir)
    print("Done recoloring all icons!")
