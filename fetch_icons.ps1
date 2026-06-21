$iconsDir = "d:\Coding_Projects\AniKin\AniKin\scripts\anikin\icons"
if (-not (Test-Path $iconsDir)) { New-Item -ItemType Directory -Force -Path $iconsDir }

$mappings = @{
    "align_all.svg" = "align-center"
    "align_translate.svg" = "move"
    "align_rotate.svg" = "rotate-cw"
    "nudge_left.svg" = "chevron-left"
    "nudge_right.svg" = "chevron-right"
    "nudge_left_fast.svg" = "chevrons-left"
    "nudge_right_fast.svg" = "chevrons-right"
    "lock.svg" = "lock"
    "unlock.svg" = "unlock"
    "settings.svg" = "settings"
    "selection_sets.svg" = "layers"
    "bake_to_locator.svg" = "box"
    "bake_from_locator.svg" = "box-select"
    "auto.svg" = "activity"
    "flat.svg" = "minus"
    "linear.svg" = "git-commit"
    "step.svg" = "list"
    "spline.svg" = "git-merge"
    "trail.svg" = "git-branch"
    "ghost.svg" = "ghost"
    "euler.svg" = "rotate-3d"
    "smooth.svg" = "wind"
    "key.svg" = "key"
    "delkey.svg" = "x-square"
    "hotkeys.svg" = "keyboard"
}

$baseUrl = "https://unpkg.com/lucide-static@0.344.0/icons/{0}.svg"

foreach ($key in $mappings.Keys) {
    $lucideName = $mappings[$key]
    $url = $baseUrl -f $lucideName
    $dest = Join-Path $iconsDir $key
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -ErrorAction Stop
        Write-Host "Downloaded $key (from $lucideName)"
    } catch {
        Write-Host "Failed to download $lucideName" -ForegroundColor Red
    }
}
