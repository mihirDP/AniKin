"""
drag_drop_install.py
AniKin Drag-and-Drop Installer.

INSTRUCTIONS:
Simply drag and drop this file from your file explorer directly into the Maya viewport!
It will automatically register the module path, inject it into your environment,
configure the userSetup.py script to auto-load AniKin on startup,
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
    safe_src_dir = src_dir.replace("\\", "/")
    mod_content = "+ AniKin 0.3.0 {}\n".format(safe_src_dir)
    
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

    # 4. Inject startup launch into userSetup.py for persistent auto-loading
    scripts_dir = os.path.join(maya_app_dir, "scripts")
    if not os.path.exists(scripts_dir):
        try:
            os.makedirs(scripts_dir)
        except Exception:
            pass
            
    user_setup_path = os.path.join(scripts_dir, "userSetup.py")
    startup_block = (
        "\n# —— AniKin Startup Launch ——\n"
        "try:\n"
        "    import maya.utils\n"
        "    def _anikin_startup():\n"
        "        try:\n"
            "            import anikin\n"
            "            anikin.launch()\n"
        "        except Exception as e:\n"
        "            print('Failed to auto-load AniKin: {}'.format(e))\n"
        "    maya.utils.executeDeferred(_anikin_startup)\n"
        "except Exception as e:\n"
        "    print('AniKin startup setup failed: {}'.format(e))\n"
        "# ———————————————————————————\n"
    )

    # Check if userSetup.py already contains AniKin launch
    has_setup = False
    if os.path.exists(user_setup_path):
        try:
            with open(user_setup_path, "r") as f:
                content = f.read()
            if "anikin.launch" in content or "AniKin Startup Launch" in content:
                has_setup = True
        except Exception:
            pass
            
    if not has_setup:
        try:
            with open(user_setup_path, "a") as f:
                f.write(startup_block)
        except Exception as e:
            cmds.warning("Could not write to userSetup.py: {}".format(e))

    # 5. Inject into current sys.path to allow immediate launch without restarting Maya
    scripts_dir_path = os.path.join(src_dir, "scripts")
    safe_scripts_dir = os.path.normpath(scripts_dir_path)
    
    if safe_scripts_dir not in sys.path:
        sys.path.insert(0, safe_scripts_dir)

    # 6. Launch the tool
    try:
        import anikin
        
        # We use reload_and_launch to ensure fresh import if the user is upgrading
        anikin.reload_and_launch()
        
        cmds.confirmDialog(
            title="AniKin Installed Successfully",
            message=(
                "AniKin has been successfully installed and registered!\n\n"
                "The toolbar has been launched at the bottom of your workspace.\n\n"
                "It is now registered to auto-load automatically on Maya startup."
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
