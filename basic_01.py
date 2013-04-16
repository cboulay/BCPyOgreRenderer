#!/usr/bin/env python
# This code is Public Domain.
"""Python-Ogre Basic Tutorial 01: The SceneNode, Entity, and SceneManager constructs."""

import ogre.renderer.OGRE as ogre
import SampleFramework as sf

class TutorialApplication (sf.Application):
    """Application class."""

    def _createScene (self):
        # Setup the ambient light.
        sceneManager = self.sceneManager
        sceneManager.ambientLight = (1.0, 1.0, 1.0)

        # Setup a mesh entity and attach it to the root scene node.
        ent1 = sceneManager.createEntity ('Hand', 'hand.mesh')
        node1 = sceneManager.getRootSceneNode().createChildSceneNode ('HandNode')
        node1.attachObject (ent1)
        node1.setScale(100,100,100)

if __name__ == '__main__':
    ta = TutorialApplication ()
    ta.go ()