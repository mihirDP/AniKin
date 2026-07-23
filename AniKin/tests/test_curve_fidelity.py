"""
test_curve_fidelity.py
Automated test suite for AniPose Pro V3.2 Curve Fidelity.
Verifies the 7-pass restore logic against silent tangent recomputation on locked keys,
dense keyframe clusters, weighted tangents, pre/post infinity, and time-scaled clips.

Usage:
Run this file using mayapy (Maya's python interpreter).
e.g., `mayapy test_curve_fidelity.py`
"""

import sys
import os
import unittest
import math

try:
    import maya.standalone
    maya.standalone.initialize(name='python')
except ImportError:
    print("WARNING: This script must be run using 'mayapy' (Maya Python).")
    sys.exit(1)
except Exception as e:
    print("Maya standalone failed to initialize: ", e)

import maya.cmds as cmds

# Add AniKin scripts path
repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.join(repo_dir, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from anikin.AniPosePro.core.curve_serializer import (
    serialize_clip, deserialize_curve, assert_curve_fidelity
)
from anikin.AniPosePro.paste import paste_clip_at_frame


class TestCurveFidelity(unittest.TestCase):

    def setUp(self):
        cmds.file(new=True, force=True)
        # Create a test locator to animate
        self.node = cmds.spaceLocator(name="test_ctrl")[0]
        self.attr = "translateY"
        self.full_attr = f"{self.node}.{self.attr}"

    def tearDown(self):
        cmds.file(new=True, force=True)

    def test_plateau_dense_cluster_fidelity(self):
        """
        Builds a dense cluster of keyframes with mixed tangent types and locks (plateau),
        serializes it, clears and pastes, then asserts sub-frame fidelity.
        """
        # Create keys
        # Clean wide arch [0 - 20], then dense cluster [20 - 30]
        cmds.setKeyframe(self.full_attr, time=0, value=0)
        cmds.setKeyframe(self.full_attr, time=10, value=10)
        cmds.setKeyframe(self.full_attr, time=20, value=0)

        # Dense plateau cluster
        for f in range(21, 31):
            cmds.setKeyframe(self.full_attr, time=f, value=math.sin(f - 20) * 0.1)

        # Configure tangents, weighted handles & locks
        cmds.keyTangent(self.full_attr, edit=True, weightedTangents=True)
        cmds.keyTangent(self.full_attr, time=(10, 10), edit=True, inAngle=45, outAngle=-45, inWeight=2.0, outWeight=2.0)
        cmds.keyTangent(self.full_attr, time=(20, 20), edit=True, lock=False) # Unlocked
        cmds.keyTangent(self.full_attr, time=(20, 20), edit=True, inAngle=10, outAngle=-30)

        # Pre/post infinity
        cmds.setInfinity(self.full_attr, preInfinite="cycle", postInfinite="cycle")

        # Duplicate object to keep as source reference for assert_curve_fidelity
        ref_node = cmds.spaceLocator(name="ref_ctrl")[0]
        ref_attr = f"{ref_node}.{self.attr}"
        cmds.copyKey(self.node, attribute=self.attr)
        cmds.pasteKey(ref_node, attribute=self.attr)

        # Serialize clip from source node
        clip = serialize_clip([self.node], 0, 30)

        # Clear keyframes on source node
        cmds.cutKey(self.node, attribute=self.attr, time=(0, 30))

        # Paste back onto source node
        paste_clip_at_frame(clip, [self.node], dest_frame=0, mode="replace")

        # Verify exact curve fidelity at 0.1 frame intervals
        assert_curve_fidelity(ref_attr, self.full_attr, start=0, end=30, sample_rate=0.1, epsilon=1e-4)

    def test_unlocked_asymmetric_tangents(self):
        """
        Ensures keys with unlocked, asymmetric tangents (different in/out angles)
        paste with perfect fidelity, and that setting one side does not affect the other.
        """
        cmds.setKeyframe(self.full_attr, time=0, value=0)
        cmds.setKeyframe(self.full_attr, time=12, value=5)
        cmds.setKeyframe(self.full_attr, time=24, value=0)

        cmds.keyTangent(self.full_attr, time=(12, 12), edit=True, lock=False)
        cmds.keyTangent(self.full_attr, time=(12, 12), edit=True, inAngle=60, outAngle=-15)

        # Save duplicate reference
        ref_node = cmds.spaceLocator(name="ref_ctrl")[0]
        ref_attr = f"{ref_node}.{self.attr}"
        cmds.copyKey(self.node, attribute=self.attr)
        cmds.pasteKey(ref_node, attribute=self.attr)

        # Serialize & clear
        clip = serialize_clip([self.node], 0, 24)
        cmds.cutKey(self.node, attribute=self.attr, time=(0, 24))

        # Paste back
        paste_clip_at_frame(clip, [self.node], dest_frame=0, mode="replace")

        # Verify
        assert_curve_fidelity(ref_attr, self.full_attr, start=0, end=24, sample_rate=0.1, epsilon=1e-4)

        # Verify lock is still False
        locked = cmds.keyTangent(self.full_attr, time=(12, 12), q=True, lock=True)[0]
        self.assertFalse(locked)

    def test_time_scale_fidelity(self):
        """
        Verify duration/frame-span on a scaled paste (e.g. 2.0x time stretch).
        """
        cmds.setKeyframe(self.full_attr, time=0, value=0)
        cmds.setKeyframe(self.full_attr, time=10, value=10)
        cmds.setKeyframe(self.full_attr, time=20, value=0)

        clip = serialize_clip([self.node], 0, 20)
        cmds.cutKey(self.node, attribute=self.attr, time=(0, 20))

        # Paste with 2.0x scale (stretched to 40 frames)
        paste_clip_at_frame(clip, [self.node], dest_frame=0, mode="replace", retime_frames=40)

        # Key times should be scaled to 0, 20, 40
        times = cmds.keyframe(self.full_attr, query=True, timeChange=True)
        self.assertEqual(times, [0.0, 20.0, 40.0])


if __name__ == '__main__':
    print("---------------------------------------------------------")
    print(" Starting AniPose Pro V3.2 Curve Fidelity Tests")
    print("---------------------------------------------------------")
    unittest.main(verbosity=2, exit=False)
    try:
        maya.standalone.uninitialize()
    except Exception:
        pass
