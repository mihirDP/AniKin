"""
drag_drop_install.py
AniKin Drag-and-Drop Installer.

INSTRUCTIONS:
Simply drag and drop this file from your file explorer directly into the Maya viewport!
It will automatically register the module path, inject it into your environment,
and launch the AniKin toolbar.
"""

import os
import sys
import maya.cmds as cmds

def onMayaDroppedPythonFile(*args, **kwargs):
    """
    This special function name is automatically recognized and executed by Maya
    when the file is dropped into the viewport.
    """
    # 1. Locate the source directory where this installer lives
    src_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Get the Maya user application directory (e.g. ~/Documents/maya)
    maya_app_dir = cmds.internalVar(userAppDir=True)
    
    # Sometimes internalVar returns a path with a trailing slash, normalize it
    maya_app_dir = os.path.normpath(maya_app_dir)
    modules_dir = os.path.join(maya_app_dir, "modules")
    
    # Create modules directory if it doesn't exist
    if not os.path.exists(modules_dir):
        try:
            os.makedirs(modules_dir)
        except Exception as e:
            cmds.confirmDialog(
                title="AniKin Install Error", 
                message="Could not create Maya modules directory:\n{}".format(e), 
                button=["OK"], icon="critical"
            )
            return

    # 3. Write the .mod file
    # The .mod file tells Maya where to find the module's scripts/icons without moving the folder.
    mod_file_path = os.path.join(modules_dir, "anikin.mod")
    
    # Maya .mod syntax: + <ModuleName> <Version> <Path>
    # Note: Maya expects forward slashes or escaped backslashes in .mod paths
    safe_src_dir = src_dir.replace("\\", "/")
    mod_content = "+ AniKin 0.1.0 {}\n".format(safe_src_dir)
    
    try:
        with open(mod_file_path, "w") as f:
            f.write(mod_content)
    except Exception as e:
        cmds.confirmDialog(
            title="AniKin Install Error", 
            message="Could not write anikin.mod to your preferences:\n{}".format(e), 
            button=["OK"], icon="critical"
        )
        return

    # 4. Inject into current sys.path to allow immediate launch without restarting Maya
    scripts_dir = os.path.join(src_dir, "scripts")
    safe_scripts_dir = os.path.normpath(scripts_dir)
    
    if safe_scripts_dir not in sys.path:
        sys.path.insert(0, safe_scripts_dir)

    # 5. Launch the tool
    try:
        import anikin
        
        # We use reload_and_launch to ensure fresh import if the user is upgrading
        anikin.reload_and_launch()
        
        cmds.confirmDialog(
            title="AniKin Installed Successfully",
            message=(
                "AniKin has been successfully installed and registered!\n\n"
                "The toolbar has been launched at the bottom of your workspace.\n\n"
                "To launch it in future sessions, run the following Python code:\n\n"
                "import anikin\n"
                "anikin.launch()"
            ),
            button=["Awesome!"],
            defaultButton="Awesome!",
            icon="information"
        )
    except Exception as e:
        cmds.confirmDialog(
            title="AniKin Install Error", 
            message="Module registered successfully, but failed to launch:\n{}".format(e), 
            button=["OK"], icon="critical"
        )
