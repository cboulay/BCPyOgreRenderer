import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI
import threading

class EventListener(ogre.FrameListener, ogre.WindowEventListener, OIS.KeyListener, OIS.JoyStickListener):
    """
    This class handles all our ogre and OIS events, mouse/keyboard/joystick
    depending on how you initialize this class. All events are handled
    using callbacks (buffered).
    """

    keyboard = None
    joy = None

    def __init__(self, renderWindow, bufferedKeys, bufferedJoy):

        # Initialize the various listener classes we are a subclass from
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        OIS.KeyListener.__init__(self)
        OIS.JoyStickListener.__init__(self)

        self.renderWindow = renderWindow

        # Create the inputManager using the supplied renderWindow
        windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")
        self.inputManager = OIS.createPythonInputSystem([("WINDOW",str(windowHnd))])

        # Attempt to get the mouse/keyboard input objects,
        # and use this same class for handling the callback functions.
        # These functions are defined later on.

        try:

            if bufferedKeys:
                self.keyboard = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, bufferedKeys)
                self.keyboard.setEventCallback(self)

            if bufferedJoy:
                self.joy = self.inputManager.createInputObjectJoyStick(OIS.OISJoyStick, bufferedJoy)
                self.joy.setEventCallback(self)

        except Exception, e: # Unable to obtain mouse/keyboard/joy input
            raise e

        # Set this to True when we get an event to exit the application
        self.quitApplication = False

        # Listen for any events directed to the window manager's close button
        ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self)
    def __del__ (self ):
        # Clean up OIS
        print "QUITING"
        self.delInputObjects()

        OIS.InputManager.destroyInputSystem(self.inputManager)
        self.inputManager = None

        ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)
        self.windowClosed(self.renderWindow)

    def delInputObjects(self):
        # Clean up the initialized input objects
        if self.keyboard:
            self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        if self.joy:
            self.inputManager.destroyInputObjectJoyStick(self.joy)

    def frameStarted(self, evt):
        """
        Called before a frame is displayed, handles events
        (also those via callback functions, as you need to call capture()
        on the input objects)

        Returning False here exits the application (render loop stops)
        """

        # Capture any buffered events and call any required callback functions
        if self.keyboard:
            self.keyboard.capture()
        if self.joy:
            self.joy.capture()

            # joystick test
            axes_int = self.joy.getJoyStickState().mAxes
            axes = []
            for i in axes_int:
                axes.append(i.abs)
            print axes

        # Neatly close our FrameListener if our renderWindow has been shut down
        if(self.renderWindow.isClosed()):
            return False

        return not self.quitApplication

### Window Event Listener callbacks ###

    def windowResized(self, renderWindow):
        pass

    def windowClosed(self, renderWindow):
        # Only close for window that created OIS
        if(renderWindow == self.renderWindow):
            del self

### Key Listener callbacks ###

    def keyPressed(self, evt):
        # Quit the application if we hit the escape button
        if evt.key == OIS.KC_ESCAPE:
            self.quitApplication = True

        if evt.key == OIS.KC_1:
            print "hello"

            return True

    def keyReleased(self, evt):
        return True

### Joystick Listener callbacks ###

    def buttonPressed(self, evt, id):
        return True

    def buttonReleased(self, evt, id):
        return True

    def axisMoved(self, evt, id):
        return True

class Application(object):

    app_title = "MyApplication"

    def go(self):
        # See Basic Tutorial 6 for details
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.createFrameListener()
        #self.setupCEGUI()
        self.startRenderLoop()
        #self.cleanUp()

    def createRoot(self):
        self.root = ogre.Root("plugins.cfg")

    # Here the resources are read from the resources.cfg
    def defineResources(self):
        rgm = ogre.ResourceGroupManager.getSingleton()
        cf = ogre.ConfigFile()

        cf.load("resources.cfg")
        seci = cf.getSectionIterator()
        while seci.hasMoreElements():
            secName = seci.peekNextKey()
            settings = seci.getNext()
            for item in settings:
                typeName = item.key
                archName = item.value
                rgm.addResourceLocation(archName, typeName, secName)


    # Create and configure the rendering system (either DirectX or OpenGL) here
    def setupRenderSystem(self): #Delete ogre.cfg to show the config dialog box
        if not self.root.restoreConfig() and not self.root.showConfigDialog():
            raise Exception("User canceled the config dialog -> Application.setupRenderSystem()")

    # Create the render window
    def createRenderWindow(self):
        self.root.initialise(True, "TEST")
        self.renderWindow = self.root.getAutoCreatedWindow()
        self.renderWindow.setDeactivateOnFocusChange(False)

    # Initialize the resources here (which were read from resources.cfg in defineResources()
    def initializeResourceGroups(self):
        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

    def setupScene(self):
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "Default SceneManager")
        self.camera = self.sceneManager.createCamera("Camera")
        self.viewPort = self.root.getAutoCreatedWindow().addViewport(self.camera)

        self.camera.setPosition(ogre.Vector3(0, 0, 400))
        self.camera.lookAt(ogre.Vector3(0, 0, 0))

        self.sceneManager.setAmbientLight(ogre.ColourValue(0.7,0.7,0.7))
        #self.sceneManager.setSkyDome(True, 'Examples/CloudySky',4, 8)
        #self.sceneManager.setFog( ogre.FOG_EXP, ogre.ColourValue(1,1,1),0.0002)
        self.light = self.sceneManager.createLight( 'lightMain')
        self.light.setPosition ( ogre.Vector3(20, 80, 50) )

        self.rn = self.sceneManager.getRootSceneNode()

        #=======================================================================
        # self.entityOgre = self.sceneManager.createEntity('Ogre','ogrehead.mesh')
        # self.nodeOgre = self.rn.createChildSceneNode('nodeOgre')
        # self.nodeOgre.setPosition(ogre.Vector3(0, 0, 0))
        # self.nodeOgre.attachObject(self.entityOgre)
        #=======================================================================

        self.entitySphere = self.sceneManager.createEntity("mySphere",ogre.SceneManager.PT_SPHERE)
        print self.entitySphere.getBoundingBox().getSize()
        self.nodeSphere = self.rn.createChildSceneNode("nodeSphere")
        self.nodeSphere.setPosition(ogre.Vector3(0, 0, 0))
        self.nodeSphere.attachObject(self.entitySphere)
        print self.entitySphere.getWorldBoundingBox().getSize()
        self.nodeSphere.setScale(1./50,1./50,1./50)


    def createFrameListener(self):
        self.eventListener = EventListener(self.renderWindow, True, False) # switch the final "False" into "True" to get joystick support
        self.root.addFrameListener(self.eventListener)

    def setupCEGUI(self):
        sceneManager = self.sceneManager

        # CEGUI - now compatible with version 0.7.x
        if CEGUI.Version__.startswith ("0.6"):
            CEGUI.SchemeManager.getSingleton().loadScheme("TaharezLookSkin.scheme")
            self.renderer = CEGUI.OgreCEGUIRenderer(self.renderWindow, ogre.RENDER_QUEUE_OVERLAY, False, 3000, sceneManager)
            self.system = CEGUI.System(self.renderer)
            CEGUI.SchemeManager.getSingleton().loadScheme("TaharezLookSkin.scheme")
        else:
            self.renderer = CEGUI.OgreRenderer.bootstrapSystem()
            self.system = CEGUI.System.getSingleton()
            CEGUI.SchemeManager.getSingleton().create("TaharezLookSkin.scheme")



        self.system.setDefaultMouseCursor("TaharezLook", "MouseArrow")
        self.system.setDefaultFont("BlueHighway-12")

        # Uncomment the following to read in a CEGUI sheet (from CELayoutEditor)
        #
        # self.mainSheet = CEGUI.WindowManager.getSingleton().loadWindowLayout("myapplication.layout")
        # self.system.setGUISheet(self.mainSheet)

    def startRenderLoop(self):
        self.root.startRendering()

    def cleanUp(self):
        # Clean up CEGUI
        print "CLEANING"
        #del self.renderer
        del self.system

        # Clean up Ogre
        #del self.exitListener
        del self.root


if __name__ == '__main__':
    ta = Application()
    def ogreFunc():
        try:
            ta.go()
        except ogre.OgreException, e:
            print e
    ogreThread = threading.Thread(target=ogreFunc)
    ogreThread.start()
    print ogreThread
