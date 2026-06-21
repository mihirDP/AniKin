$baseDir = "d:\Coding_Projects\AniKin\AniKin\scripts\anikin"
$toolsDir = Join-Path $baseDir "tools"

$moduleMap = [ordered]@{
    "tween.py" = "AniTween"
    "anim_offset.py" = "AniOffset"
    "smart_bake.py" = "AniBake"
    "pose.py" = "AniMirror"
    "ghosting.py" = "AniGhost"
    "motion_trail.py" = "AniMotion"
    "align.py" = "AniAlign"
    "channels.py" = "AniChannels"
    "hotkeys.py" = "AniHotkeys"
    "key_nav.py" = "AniKeyNav"
    "nudge.py" = "AniNudge"
    "selection_sets.py" = "AniSets"
    "smooth.py" = "AniSmooth"
    "tangents.py" = "AniTangents"
}

# 1. Create module directories and move files
foreach ($oldFile in $moduleMap.Keys) {
    $newMod = $moduleMap[$oldFile]
    $oldPath = Join-Path $toolsDir $oldFile
    if (Test-Path $oldPath) {
        $newModDir = Join-Path $baseDir $newMod
        if (-not (Test-Path $newModDir)) {
            New-Item -ItemType Directory -Path $newModDir | Out-Null
        }
        $newPath = Join-Path $newModDir "core.py"
        Move-Item -Path $oldPath -Destination $newPath -Force
        
        # Create __init__.py mapping the functions
        $initPath = Join-Path $newModDir "__init__.py"
        Set-Content -Path $initPath -Value "from .core import *" -Encoding UTF8
    }
}

# 2. Update imports in all python files
$allPyFiles = @()
$allPyFiles += Get-ChildItem -Path $baseDir -Filter "*.py" -Recurse
$allPyFiles += Get-ChildItem -Path "d:\Coding_Projects\AniKin\AniKin\tests" -Filter "*.py" -Recurse

foreach ($file in $allPyFiles) {
    $content = Get-Content -Path $file.FullName -Raw
    $originalContent = $content
    
    foreach ($oldFile in $moduleMap.Keys) {
        $newMod = $moduleMap[$oldFile]
        $oldModName = $oldFile.Replace(".py", "")
        
        # Replace word matches to prevent partial matching bugs
        $content = $content -replace "\banikin\.tools import $oldModName\b", "anikin import $newMod"
        $content = $content -replace "\banikin\.tools\.$oldModName\b", "anikin.$newMod"
        $content = $content -replace "\b$oldModName\.", "$newMod."
    }
    
    if ($content -cne $originalContent) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
    }
}
Write-Host "Refactoring complete."
