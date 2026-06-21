"""
test_anikin_api.py
Automated test suite for AniKin logic API using maya standalone.

Usage: 
Run this file using mayapy (Maya's python interpreter).
e.g., `mayapy test_anikin_api.py`
"""

import sys
import os
import unittest

# Try initializing maya standalone
try:
    import maya.standalone
    maya.standalone.initialize(name='python')
except ImportError:
    print("WARNING: This script must be run using 'mayapy' (Maya Python).")
    print("Cannot import maya.cmds or maya.standalone.")
    sys.exit(1)
except Exception as e:
    print("Maya standalone failed to initialize: ", e)

import maya.cmds as cmds

# Add AniKin to sys.path so we can import it
repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.join(repo_dir, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from anikin import AniAlign, AniNudge, AniOffset, AniChannels, AniBake, AniTangents

class TestAniKinAPI(unittest.TestCase):
    
    def setUp(self):
        """Creates a clean test scene before each test."""
        cmds.file(new=True, force=True)

    def test_align_translation(self):
        """Test aligning the translation of an object to a target."""
        obj1 = cmds.polyCube(name="cube1")[0]
        obj2 = cmds.polySphere(name="sphere1")[0]
        
        cmds.setAttr(obj2 + ".translate", 10, 5, 2)
        
        # Select obj1 then obj2 (target)
        cmds.select([obj1, obj2], replace=True)
        
        # Execute align translation only
        AniAlign.execute(translate=True, rotate=False)
        
        # Verify
        pos = cmds.getAttr(obj1 + ".translate")[0]
        self.assertAlmostEqual(pos[0], 10.0, places=4)
        self.assertAlmostEqual(pos[1], 5.0, places=4)
        self.assertAlmostEqual(pos[2], 2.0, places=4)

    def test_align_rotation(self):
        """Test aligning the rotation of an object to a target."""
        obj1 = cmds.polyCube(name="cube1")[0]
        obj2 = cmds.polySphere(name="sphere1")[0]
        
        cmds.setAttr(obj2 + ".rotate", 45, 30, 60)
        
        cmds.select([obj1, obj2], replace=True)
        AniAlign.execute(translate=False, rotate=True)
        
        rot = cmds.getAttr(obj1 + ".rotate")[0]
        self.assertAlmostEqual(rot[0], 45.0, places=4)
        self.assertAlmostEqual(rot[1], 30.0, places=4)
        self.assertAlmostEqual(rot[2], 60.0, places=4)

    def test_nudge_keys(self):
        """Test nudging keyframes left and right."""
        obj = cmds.polyCube(name="cube1")[0]
        
        # Set keys at frame 10 and 20
        cmds.setKeyframe(obj, attribute='translateX', time=10, value=0)
        cmds.setKeyframe(obj, attribute='translateX', time=20, value=5)
        
        # Select keyframes and nudge +5
        cmds.selectKey(obj, time=(10, 20))
        AniNudge.execute(5)
        
        # Verify new times are 15 and 25
        times = cmds.keyframe(obj, attribute='translateX', query=True, timeChange=True)
        self.assertEqual(times, [15.0, 25.0])

    def test_anim_offset(self):
        """Test staggering animation across multiple objects."""
        obj1 = cmds.polyCube(name="cube1")[0]
        obj2 = cmds.polyCube(name="cube2")[0]
        
        cmds.setKeyframe(obj1, attribute='translateX', time=10, value=0)
        cmds.setKeyframe(obj2, attribute='translateX', time=10, value=0)
        
        cmds.select([obj1, obj2], replace=True)
        AniOffset.execute(offset_frames=2)
        
        # obj1 should be unchanged (base object), obj2 should be offset by +2
        times1 = cmds.keyframe(obj1, attribute='translateX', query=True, timeChange=True)
        times2 = cmds.keyframe(obj2, attribute='translateX', query=True, timeChange=True)
        
        self.assertEqual(times1[0], 10.0)
        self.assertEqual(times2[0], 12.0)

    def test_channels_lock_unlock(self):
        """Test locking and unlocking channel box attributes."""
        obj = cmds.polyCube(name="cube1")[0]
        cmds.select(obj)
        
        AniChannels.lock_channels() # Should lock all keyable since none highlighted
        
        self.assertTrue(cmds.getAttr(obj + ".tx", lock=True))
        
        AniChannels.unlock_channels()
        self.assertFalse(cmds.getAttr(obj + ".tx", lock=True))

    def tearDown(self):
        cmds.file(new=True, force=True)

if __name__ == '__main__':
    print("---------------------------------------------------------")
    print(" Starting AniKin API QA Tests")
    print("---------------------------------------------------------")
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    try:
        maya.standalone.uninitialize()
    except Exception:
        pass

