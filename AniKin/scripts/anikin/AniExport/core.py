"""
AniExport.py
Export with Unreal validation checks.
"""

import maya.cmds as cmds
import os
import maya.mel as mel
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


class ExportValidator(object):
    """Runs pre-export validation checks and collects pass/fail results."""

    def __init__(self, export_target="unreal"):
        self.target = export_target
        self.results = []  # [(check_name, passed, message)]

    def run_all(self):
        self.results = []
        self._check_root_bone()
        self._check_units()
        self._check_framerate()
        self._check_unbaked_constraints()
        self._check_namespaces()
        self._check_negative_scale()
        self._check_anim_range()
        return self.results

    def all_critical_pass(self):
        critical = [r for r in self.results if r[0].startswith("CRITICAL")]
        return all(r[1] for r in critical)

    def _check_root_bone(self):
        joints = cmds.ls(type="joint")
        roots = [j for j in joints if not cmds.listRelatives(j, parent=True, type="joint")]
        if not roots:
            self.results.append(("CRITICAL_root_bone", False, "No root joint found."))
        elif len(roots) > 1:
            self.results.append(("CRITICAL_root_bone", False,
                                 "Multiple root joints: {}".format(roots)))
        else:
            root = roots[0]
            pos = cmds.xform(root, query=True, worldSpace=True, translation=True)
            at_origin = all(abs(v) < 0.001 for v in pos)
            self.results.append((
                "CRITICAL_root_bone",
                at_origin,
                "OK" if at_origin else "Root '{}' not at world origin on frame 1.".format(root)
            ))

    def _check_units(self):
        unit = cmds.currentUnit(query=True, linear=True)
        expected = "cm"
        passed = unit == expected
        self.results.append((
            "CRITICAL_units", passed,
            "OK" if passed else "Unit is '{}' — expected '{}'.".format(unit, expected)
        ))

    def _check_framerate(self):
        current_fps_str = cmds.currentUnit(query=True, time=True)
        self.results.append((
            "WARNING_framerate", True,
            "Scene framerate: {}. Verify against target spec.".format(current_fps_str)
        ))

    def _check_unbaked_constraints(self):
        constraints = cmds.ls(type=["parentConstraint", "pointConstraint",
                                     "orientConstraint", "scaleConstraint"])
        self.results.append((
            "CRITICAL_constraints",
            not bool(constraints),
            "OK" if not constraints else "Unbaked constraints found — bake before export."
        ))

    def _check_namespaces(self):
        non_default = [ns for ns in cmds.namespaceInfo(listOnlyNamespaces=True,
                                                        recurse=True)
                       if ns not in ("UI", "shared")]
        self.results.append((
            "WARNING_namespaces",
            not bool(non_default),
            "OK" if not non_default else "Non-default namespaces: {}.".format(non_default)
        ))

    def _check_negative_scale(self):
        joints = cmds.ls(type="joint")
        bad = []
        for j in joints:
            sx, sy, sz = cmds.getAttr("{}.scale".format(j))[0]
            if sx < 0 or sy < 0 or sz < 0:
                bad.append(j)
        self.results.append((
            "CRITICAL_negative_scale",
            not bool(bad),
            "OK" if not bad else "Negative scale joints: {}.".format(bad)
        ))

    def _check_anim_range(self):
        start = cmds.playbackOptions(query=True, animationStartTime=True)
        end = cmds.playbackOptions(query=True, animationEndTime=True)
        passed = end > start
        self.results.append((
            "CRITICAL_anim_range", passed,
            "OK" if passed else "Animation end ({}) must be after start ({}).".format(end, start)
        ))


def export_fbx(filepath, validator=None):
    """
    Runs validation, prompts on failure, then exports FBX.
    """
    if validator is None:
        validator = ExportValidator()

    validator.run_all()

    if not validator.all_critical_pass():
        failed = [r for r in validator.results if not r[1] and r[0].startswith("CRITICAL")]
        msg = "\n".join("• {}".format(r[2]) for r in failed)
        result = cmds.confirmDialog(
            title="AniKin Export — Critical Checks Failed",
            message="The following issues must be resolved:\n\n{}\n\nExport anyway?".format(msg),
            button=["Export Anyway", "Cancel"],
            defaultButton="Cancel"
        )
        if result == "Cancel":
            return False

    # Execute FBX export via MEL
    try:
        cmds.loadPlugin("fbxmaya", quiet=True)
        mel_cmd = 'FBXExport -f "{}" -s'.format(filepath.replace("\\", "/"))
        mel.eval(mel_cmd)
        
        cmds.inViewMessage(
            amg="<hl>AniKin</hl>: Exported FBX to " + os.path.basename(filepath),
            pos="topCenter", fade=True, fadeStayTime=1500
        )
        return True
    except Exception as e:
        cmds.warning("AniKin: FBX Export failed: {}".format(e))
        return False
