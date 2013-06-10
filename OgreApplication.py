import sys
import os
import os.path
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS

def getPluginPath():
    """ Return the absolute path to a valid plugins.cfg file.
    look in the current directory for plugins.cfg followed by plugins.cfg.nt|linux|mac
    If not found look one directory up
    """

    paths = [os.path.join(os.getcwd(), 'plugins.cfg'),
             os.path.join(os.getcwd(), 'BCPyOgreRenderer', 'plugins.cfg'),
             os.path.join(os.getcwd(), '..','plugins.cfg'),
             ]
    if os.sys.platform == 'darwin':
        paths.insert(1, os.path.join(os.getcwd(), 'plugins.cfg.mac'))
        paths.append(os.path.join(os.getcwd(), '..', 'plugins.cfg.mac'))
    else:
        paths.insert(1,os.path.join(os.getcwd(), 'plugins.cfg.'+os.name))
        paths.append(os.path.join(os.getcwd(), '..', 'plugins.cfg.'+os.name))

    for path in paths:
        if os.path.exists(path):
            return path

    sys.stderr.write("\n"
        "** Warning: Unable to locate a suitable plugins.cfg file.\n"
        "** Warning: Please check your ogre installation and copy a\n"
        "** Warning: working plugins.cfg file to the current directory.\n\n")
    raise ogre.Exception(0, "can't locate a suitable 'plugins' file", "")

def isUnitTest():
    """ use an environment variable to define that we need to do unittesting"""
    env = os.environ
    if env.has_key ("PythonOgreUnitTestPath"):
        return True
    return False

def UnitTest_Duration():
    return 5

def UnitTest_Screenshot():
    if isUnitTest():
        env = os.environ
        path = env["PythonOgreUnitTestPath"]
        parentpath = os.getcwd().split(os.path.sep)[-1] # get the last part of the parent directory
        filename = parentpath+'.'+ sys.modules['__main__'].__file__.split('.')[0] # file name is parent.demo.xx
        path = os.path.join ( path, filename )
        return path
    else:
        return "test"

class Application(object):
    debugText=""
    app_title = "MyApplication"

    def fakeIt(self):
        """Set some self variables that would normally be set by the BCPy Renderer wrapper."""
        import BCPy2000.AppTools.Coords as Coords
        self._plugins_path = None
        self._resource_path = None
        self._coords = Coords.Box(left=0, top=0, width=800, height=600, sticky=True, anchor='top left')
        self._screen_scale = 0.9
        self._screen_params = {
                                "monitorIndex": 0,
                                "left": 0,
                                "top": 0,
                                "title": "MyApplication"
                               }

    def go(self):
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.createFrameListener()
        #self.setupCEGUI()
        self.startRenderLoop()
        self.cleanUp()

    # The Root constructor for the ogre
    def createRoot(self):
        if self._plugins_path is None:
            self._plugins_path = getPluginPath()
        if self._resource_path is None:
            self._resource_path = os.path.join(os.path.dirname(self._plugins_path),'resources.cfg')
        self.root = ogre.Root(self._plugins_path)

    # Here the resources are read from the resources.cfg
    def defineResources(self):
        rgm = ogre.ResourceGroupManager.getSingleton()
        cf = ogre.ConfigFile()
        cf.load(self._resource_path)
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

        #=======================================================================
        # self.root.initialise(True, self._screen_params["title"])
        # self.renderWindow = self.root.getAutoCreatedWindow()
        #=======================================================================

        self.root.initialise(False)
        hWnd = 0  # Get the hWnd of the application!
        misc = ogre.NameValuePairList()
        misc["externalWindowHandle"] = str(int(hWnd))
        if self._screen_params["monitorIndex"] == -1:
           try:
               self._screen_params["monitorIndex"] = self.root.getDisplayMonitorCount()-1 #Only newer versions of Ogre
           except:
               import BCPy2000.AppTools.Displays as Displays
               self._screen_params["monitorIndex"] = len(Displays.monitors())-1
        #misc["border"] = self._screen_params["border"] #Causes unexpected behavior
        misc["left"] = str(int(self._screen_params["left"]))
        misc["top"] = str(int(self._screen_params["top"]))
        #misc["monitorIndex"] = str(int(self._screen_params["monitorIndex"])) #Doesn't seem to work :(
        if self._screen_scale:
           pass#TODO: Get the size of the monitor and scale it if a scale is provided
        scrw,scrh = int(self._coords.width), int(self._coords.height)
        self.renderWindow = self.root.createRenderWindow(self._screen_params["title"], scrw, scrh, False, misc)
        self.renderWindow.setDeactivateOnFocusChange(False)

    # Initialize the resources here (which were read from resources.cfg in defineResources()
    def initializeResourceGroups(self):
        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

    # Now, create a scene here. Three things that MUST BE done are sceneManager, camera and
    # viewport initializations
    def setupScene(self):
        #Create and configure the scene manager
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "Default SceneManager")
        self.sceneManager.setAmbientLight(ogre.ColourValue(0.9, 0.9, 0.9))
        #self.sceneManager.setSkyDome(True, 'Examples/CloudySky',4, 8)
        #self.sceneManager.setFog( ogre.FOG_EXP, ogre.ColourValue(1,1,1),0.0005)

        #Create and configure the camera
        self.camera = self.sceneManager.createCamera("Camera")

        #Create and configure the viewPort
        self.viewPort = self.renderWindow.addViewport(self.camera)
        #self.viewPort.setBackgroundColour(self._bgcolor)

        #Place the camera as far from the 0 plane as the larger of the screen size
        scrw,scrh = self.viewPort.getActualWidth(), self.viewPort.getActualHeight()
        longd = max(scrw,scrh)
        self.camera.setPosition( ogre.Vector3(0, 0, longd) )
        self.camera.lookAt( ogre.Vector3(0, 0, 0) )
        self.camera.setNearClipDistance(round(longd/10))
        self.camera.setAutoAspectRatio(True);

        #Add a light source
        self.light = self.sceneManager.createLight("Light1")
        #light.type = ogre.Light.LT_POINT
        self.light.setPosition ( ogre.Vector3(scrw, scrh, longd/5.0) )
        self.light.diffuseColour = 0.5, 0.5, 0.5
        self.light.specularColour = 0.3, 0.3, 0.3

        #self.coordinate_mapping = self._coordinate_mapping

    def createFrameListener(self):
        """Creates the FrameListener."""
        #,self.frameListener, self.frameListener.Mouse
        self.frameListener = FrameListener(self.renderWindow, self.camera)
        #self.frameListener.unittest = self.unittest
        #self.frameListener.showDebugOverlay(True)
        self.frameListener.showDebugOverlay(False)
        self.root.addFrameListener(self.frameListener)

    def startRenderLoop(self):
        self.root.startRendering()

    def cleanUp(self):
        # Clean up Ogre
        self.root.shutdown()
        del self.root

class FrameListener(ogre.FrameListener, ogre.WindowEventListener):
    """A default frame listener, which takes care of basic mouse and keyboard
    input."""

    def __init__(self, renderWindow, camera, bufferedKeys = False, bufferedMouse = False, bufferedJoy = False):
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        self.camera = camera
        self.renderWindow = renderWindow
        self.statisticsOn = True
        self.numScreenShots = 0
        self.timeUntilNextToggle = 0
        self.sceneDetailIndex = 0
        self.moveScale = 0.0
        self.rotationScale = 0.0
        self.translateVector = ogre.Vector3(0.0,0.0,0.0)
        self.filtering = ogre.TFO_BILINEAR
        self.showDebugOverlay(True)
        self.rotateSpeed =  ogre.Degree(36)
        self.moveSpeed = 100.0
        self.rotationSpeed = 8.0
        self.displayCameraDetails = False
        self.bufferedKeys = bufferedKeys
        self.bufferedMouse = bufferedMouse
        self.rotationX = ogre.Degree(0.0)
        self.rotationY = ogre.Degree(0.0)
        self.bufferedJoy = bufferedJoy
        self.shouldQuit = False # set to True to exit..
        self.MenuMode = False   # lets understand a simple menu function

        self.unittest = isUnitTest()
        self.unittest_duration = UnitTest_Duration()  # seconds before screen shot a exit
#         self.unittest_screenshot = sys.modules['__main__'].__file__.split('.')[0]     # file name for unittest screenshot
        self.unittest_screenshot = UnitTest_Screenshot()
        ## we can tell if we are using OgreRefapp based upon the camera class

        if self.camera.__class__ == ogre.Camera:
            self.RefAppEnable = False
        else:
            self.RefAppEnable = True
        self._setupInput()
        self._registeredAnimStates = []

    def __del__ (self ):
      ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)
      self.windowClosed(self.renderWindow)

    def _inputSystemParameters (self ):
        """ ovreride to extend any OIS system parameters
        """
        return []

    def _setupInput(self):
         # ignore buffered input

         # FIXME: This should be fixed in C++ propbably
         import platform
         int64 = False
         for bit in platform.architecture():
             if '64' in bit:
                 int64 = True
         if int64:
             windowHnd = self.renderWindow.getCustomAttributeUnsignedLong("WINDOW")
         else:
             windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")

         #
         # Here is where we create the OIS input system using a helper function that takes python list of tuples
         #
         t= self._inputSystemParameters()
         params = [("WINDOW",str(windowHnd))]
         params.extend(t)
         self.InputManager = OIS.createPythonInputSystem( params )

         #
         # an alternate way is to use a multimap which is exposed in ogre
         #
#          pl = ogre.SettingsMultiMap()
#          windowHndStr = str(windowHnd)
#          pl.insert("WINDOW", windowHndStr)
#          for  v in self._inputSystemParameters():
#               pl.insert(v[0],v[1])
#          im = OIS.InputManager.createInputSystem( pl )

         #Create all devices (We only catch joystick exceptions here, as, most people have Key/Mouse)
         self.Keyboard = self.InputManager.createInputObjectKeyboard( OIS.OISKeyboard, self.bufferedKeys )
         self.Mouse = self.InputManager.createInputObjectMouse( OIS.OISMouse, self.bufferedMouse )
         try:
            self.Joy = self.InputManager.createInputObjectJoyStick( OIS.OISJoyStick, self.bufferedJoy )
         except:
            self.Joy = False
#
         #Set initial mouse clipping size
         self.windowResized(self.renderWindow)

         self.showDebugOverlay(True)

         #Register as a Window listener
         ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self);



    def setMenuMode(self, mode):
        self.MenuMode = mode

    def _UpdateSimulation( self, frameEvent ):
        # create a real version of this to update the simulation
        pass

    def windowResized (self, rw):
         dummyint = 0
         width, height, depth, left, top= rw.getMetrics(dummyint,dummyint,dummyint, dummyint, dummyint)  # Note the wrapped function as default needs unsigned int's
         ms = self.Mouse.getMouseState()
         ms.width = width
         ms.height = height

    def windowClosed(self, rw):
      #Only close for window that created OIS (mWindow)
      if( rw == self.renderWindow ):
         if( self.InputManager ):
            self.InputManager.destroyInputObjectMouse( self.Mouse )
            self.InputManager.destroyInputObjectKeyboard( self.Keyboard )
            if self.Joy:
                self.InputManager.destroyInputObjectJoyStick( self.Joy )
            OIS.InputManager.destroyInputSystem(self.InputManager)
            self.InputManager=None

    ## NOTE the in Ogre 1.6 (1.7) this is changed to frameRenderingQueued !!!
    def frameRenderingQueued ( self, evt ):
        if(self.renderWindow.isClosed() or self.shouldQuit ):
            return False
        if self.unittest:
            self.unittest_duration -= evt.timeSinceLastFrame
            if self.unittest_duration < 0:
                self.renderWindow.writeContentsToFile(self.unittest_screenshot + '.jpg')
                return False
        ##Need to capture/update each device - this will also trigger any listeners
        self.Keyboard.capture()
        self.Mouse.capture()
        buffJ = True
        if( self.Joy ):
            self.Joy.capture()
            buffJ = self.Joy.buffered()

        ##Check if one of the devices is not buffered
        if not self.Mouse.buffered() or not self.Keyboard.buffered() or not buffJ :
            ## one of the input modes is immediate, so setup what is needed for immediate movement
            if self.timeUntilNextToggle >= 0:
                self.timeUntilNextToggle -= evt.timeSinceLastFrame

            ## Move about 100 units per second
            self.moveScale = self.moveSpeed * evt.timeSinceLastFrame
            ## Take about 10 seconds for full rotation
            self.rotScale = self.rotateSpeed * evt.timeSinceLastFrame

        self.rotationX = ogre.Degree(0.0)
        self.rotationY = ogre.Degree(0.0)
        self.translateVector = ogre.Vector3().ZERO

        ##Check to see which device is not buffered, and handle it
        if not self.Keyboard.buffered():
            if  not self._processUnbufferedKeyInput(evt):
                return False
        if not self.Mouse.buffered():
            if not self._processUnbufferedMouseInput(evt):
                return False

        if not self.Mouse.buffered() or not self.Keyboard.buffered() or not buffJ:
            self._moveCamera()

        return True


#     def frameStarted(self, frameEvent):
#         return True
#
#         if self.timeUntilNextToggle >= 0:
#             self.timeUntilNextToggle -= frameEvent.timeSinceLastFrame
#
#         if frameEvent.timeSinceLastFrame == 0:
#             self.moveScale = 1
#             self.rotationScale = 0.1
#         else:
#             self.moveScale = self.moveSpeed * frameEvent.timeSinceLastFrame
#             self.rotationScale = self.rotationSpeed * frameEvent.timeSinceLastFrame
#
#         self.rotationX = ogre.Degree(0.0)
#         self.rotationY = ogre.Degree(0.0)
#         self.translateVector = ogre.Vector3(0.0, 0.0, 0.0)
#         if not self._processUnbufferedKeyInput(frameEvent):
#             return False
#
#         if not self.MenuMode:   # if we are in Menu mode we don't move the camera..
#             self._processUnbufferedMouseInput(frameEvent)
#         self._moveCamera()
#         # Perform simulation step only if using OgreRefApp.  For simplicity create a function that simply does
#         ###  "OgreRefApp.World.getSingleton().simulationStep(frameEvent.timeSinceLastFrame)"
#
#         if  self.RefAppEnable:
#             self._UpdateSimulation( frameEvent )
#         return True

    def frameEnded(self, frameEvent):
        if self.statisticsOn:
            self._updateStatistics()
        return True

    def showDebugOverlay(self, show):
        """Turns the debug overlay (frame statistics) on or off."""
        overlay = ogre.OverlayManager.getSingleton().getByName('POCore/DebugOverlay')
        if overlay is None:
            self.statisticsOn = False
            ogre.LogManager.getSingleton().logMessage( "ERROR in sf_OIS.py: Could not find overlay POCore/DebugOverlay" )
            return
        if show:
            overlay.show()
        else:
            overlay.hide()

    def _processUnbufferedKeyInput(self, frameEvent):
        if self.Keyboard.isKeyDown(OIS.KC_A):
            self.translateVector.x = -self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_D):
            self.translateVector.x = self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_UP) or self.Keyboard.isKeyDown(OIS.KC_W):
            self.translateVector.z = -self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_DOWN) or self.Keyboard.isKeyDown(OIS.KC_S):
            self.translateVector.z = self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_PGUP):
            self.translateVector.y = self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_PGDOWN):
            self.translateVector.y = - self.moveScale

        if self.Keyboard.isKeyDown(OIS.KC_RIGHT):
            self.rotationX = - self.rotationScale

        if self.Keyboard.isKeyDown(OIS.KC_LEFT):
            self.rotationX = self.rotationScale

        #=======================================================================
        # if self.Keyboard.isKeyDown(OIS.KC_ESCAPE) or self.Keyboard.isKeyDown(OIS.KC_Q):
        #    return False
        #=======================================================================

        if( self.Keyboard.isKeyDown(OIS.KC_F) and self.timeUntilNextToggle <= 0 ):
             self.statisticsOn = not self.statisticsOn
             self.showDebugOverlay(self.statisticsOn)
             self.timeUntilNextToggle = 1

        if self.Keyboard.isKeyDown(OIS.KC_T) and self.timeUntilNextToggle <= 0:
            if self.filtering == ogre.TFO_BILINEAR:
                self.filtering = ogre.TFO_TRILINEAR
                self.Aniso = 1
            elif self.filtering == ogre.TFO_TRILINEAR:
                self.filtering = ogre.TFO_ANISOTROPIC
                self.Aniso = 8
            else:
                self.filtering = ogre.TFO_BILINEAR
                self.Aniso = 1

            ogre.MaterialManager.getSingleton().setDefaultTextureFiltering(self.filtering)
            ogre.MaterialManager.getSingleton().setDefaultAnisotropy(self.Aniso)
            self.showDebugOverlay(self.statisticsOn)
            self.timeUntilNextToggle = 1

        if self.Keyboard.isKeyDown(OIS.KC_SYSRQ) and self.timeUntilNextToggle <= 0:
            path = 'screenshot_%d.png' % self.numScreenShots
            self.numScreenShots += 1
            self.renderWindow.writeContentsToFile(path)
            Application.debugText = 'screenshot taken: ' + path
            self.timeUntilNextToggle = 0.5

        if self.Keyboard.isKeyDown(OIS.KC_R) and self.timeUntilNextToggle <= 0:
            detailsLevel = [ ogre.PM_SOLID,
                             ogre.PM_WIREFRAME,
                             ogre.PM_POINTS ]
            self.sceneDetailIndex = (self.sceneDetailIndex + 1) % len(detailsLevel)
            self.camera.polygonMode=detailsLevel[self.sceneDetailIndex]
            self.timeUntilNextToggle = 0.5

        if self.Keyboard.isKeyDown(OIS.KC_F) and self.timeUntilNextToggle <= 0:
            self.statisticsOn = not self.statisticsOn
            self.showDebugOverlay(self.statisticsOn)
            self.timeUntilNextToggle = 1

        if self.Keyboard.isKeyDown(OIS.KC_P) and self.timeUntilNextToggle <= 0:
            self.displayCameraDetails = not self.displayCameraDetails
            if not self.displayCameraDetails:
                Application.debugText = ""

        if self.displayCameraDetails:
            # Print camera details
            pos = self.camera.getDerivedPosition()
            o = self.camera.getDerivedOrientation()
            Application.debugText = "P: %.3f %.3f %.3f O: %.3f %.3f %.3f %.3f"  \
                        % (pos.x,pos.y,pos.z, o.w,o.x,o.y,o.z)
        return True

    def _isToggleKeyDown(self, keyCode, toggleTime = 1.0):
        if self.Keyboard.isKeyDown(keyCode)and self.timeUntilNextToggle <=0:
            self.timeUntilNextToggle = toggleTime
            return True
        return False

    def _isToggleMouseDown(self, Button, toggleTime = 1.0):
        ms = self.Mouse.getMouseState()
        if ms.buttonDown( Button ) and self.timeUntilNextToggle <=0:
            self.timeUntilNextToggle = toggleTime
            return True
        return False

    def _processUnbufferedMouseInput(self, frameEvent):
        ms = self.Mouse.getMouseState()
        if ms.buttonDown( OIS.MB_Right ):
            self.translateVector.x += ms.X.rel * 0.13
            self.translateVector.y -= ms.Y.rel * 0.13
        else:
            self.rotationX = ogre.Degree(- ms.X.rel * 0.13)
            self.rotationY = ogre.Degree(- ms.Y.rel * 0.13)
        return True

    def _moveCamera(self):
        self.camera.yaw(self.rotationX)
        self.camera.pitch(self.rotationY)
#         try:
#             self.camera.translate(self.translateVector) # for using OgreRefApp
#         except AttributeError:
        self.camera.moveRelative(self.translateVector)

    def _updateStatistics(self):
        statistics = self.renderWindow
        self._setGuiCaption('POCore/AverageFps', 'Avg FPS: %u' % statistics.getAverageFPS())
        self._setGuiCaption('POCore/CurrFps', 'FPS: %u' % statistics.getLastFPS())
#         self._setGuiCaption('POCore/BestFps',
#                              'Best FPS: %f %d ms' % (statistics.getBestFPS(), statistics.getBestFrameTime()))
#         self._setGuiCaption('POCore/WorstFps',
#                              'Worst FPS: %f %d ms' % (statistics.getWorstFPS(), statistics.getWorstFrameTime()))
        self._setGuiCaption('POCore/NumTris', 'Trianges: %u' % statistics.getTriangleCount())
        self._setGuiCaption('POCore/NumBatches', 'Batches: %u' % statistics.batchCount)

        self._setGuiCaption('POCore/DebugText', Application.debugText)

    def _setGuiCaption(self, elementName, text):
        element = ogre.OverlayManager.getSingleton().getOverlayElement(elementName, False)
        ##d=ogre.UTFString("hell0")
        ##element.setCaption(d)

        #element.caption="hello"

        #element.setCaption("help")
        element.setCaption(text) # ogre.UTFString(text))


if __name__ == '__main__':
    import threading
    ta = Application()
    def ogreFunc():
        try:
            ta.fakeIt()
            ta.go()
        except ogre.OgreException, e:
            print e
    ogreThread = threading.Thread(target=ogreFunc)
    ogreThread.start()
    print ogreThread