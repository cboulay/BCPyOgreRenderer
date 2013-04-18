#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application
#TODO: ImageStimulus
#TODO: Block
#TODO: Disc
#TODO: Keyboard events passed to application
#TODO: Framerate
#TODO: Fonts

__all__ = ['Text', 'Block', 'Disc', 'ImageStimulus', 'Movie']

import os
import sys
import time
import numpy
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS

import AppTools.Coords as Coords
try:    from BCI2000PythonApplication    import BciGenericRenderer, BciStimulus   # development copy
except: from BCPy2000.GenericApplication import BciGenericRenderer, BciStimulus   # installed copy

class OgreRenderer(BciGenericRenderer):

    def __init__(self):
        #Set some defaults
        self._coords = Coords.Box(left=100, top=100, width=800, height=600, sticky=True, anchor='top left')
        self._bgcolor = (0.5, 0.5, 0.5)
        self.framerate = 60.
        self.changemode = False
        self.frameless_window = False
        self.always_on_top = False
        self.title = 'stimuli'
        self.coordinate_mapping = 'pixels from lower left' # VisionEgg-like
        self.screen = None
        self._bci = None

    def setup(self, left = None, top = None, width = None, height = None,
        bgcolor = None, framerate = None, changemode = None,
        frameless_window = None, always_on_top = None, title=None,
        coordinate_mapping = None,
        plugins_path = 'plugins.cfg.nt', resource_path = 'resources.cfg',
        **kwds):
        #Set any constants that may come from the parameters.
        #Called during application preflight on the main thread
        self.plugins_path = plugins_path
        self.resource_path = resource_path

    def Initialize(self, bci=None):
        #Called after generic preflights, after generic _Initialize, but before application Initialize
        #On the 'visual display' thread
        self._bci = bci
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        #self.createFrameListener()
        #self.setupInputSystem()

    # The Root constructor for the ogre
    def createRoot(self):
        self.root = ogre.Root(self.plugins_path)

    # Here the resources are read from the resources.cfg
    def defineResources(self):
        rgm = ogre.ResourceGroupManager.getSingleton()
        cf = ogre.ConfigFile()

        cf.load(self.resource_path)
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
        self.root.initialise(True, self.title)
        self.renderWindow = self.root.getAutoCreatedWindow()
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
        self.sceneManager.setAmbientLight(ogre.ColourValue(0.7, 0.7, 0.7))
        #self.sceneManager.setSkyDome(True, 'Examples/CloudySky',4, 8)
        self.sceneManager.setFog( ogre.FOG_EXP, ogre.ColourValue(1,1,1),0.0005)

        #Create and configure the camera
        self.camera = self.sceneManager.createCamera("Camera")
        self.camera.setPosition( ogre.Vector3(0, 0, -400) )
        self.camera.lookAt( ogre.Vector3(0, 0, 0) )
        self.camera.setNearClipDistance(15)

        #Create and configure the viewPort
        self.viewPort = self.root.getAutoCreatedWindow().addViewport(self.camera)
        self.viewPort.setBackgroundColour(self._bgcolor)

        #Add a light source
        light = self.sceneManager.createLight("Light1")
        #light.type = ogre.Light.LT_POINT
        light.setPosition ( ogre.Vector3(20, 80, 50) )
        light.diffuseColour = 1, 1, 1
        light.specularColour = 1, 1, 1

    # here setup the input system (OIS is the one preferred with Ogre3D)
    def setupInputSystem(self):
        windowHandle = self.renderWindow.getCustomAttributeInt("WINDOW")
        paramList = [("WINDOW", str(windowHandle))]
        self.inputManager = OIS.createPythonInputSystem(paramList)
        # Now InputManager is initialized for use. Keyboard and Mouse objects
        # must still be initialized separately
        try:
            self.keyboard = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, False)
            self.mouse = self.inputManager.createInputObjectMouse(OIS.OISMouse, False)
        except Exception, e:
            raise e

    #===========================================================================
    # def createFrameListener(self):
    #    self.eventListener = EventListener(self.renderWindow, True, True, False) # switch the final "False" into "True" to get joystick support
    #    self.root.addFrameListener(self.eventListener)
    #===========================================================================

    def GetFrameRate(self):
        return self.framerate#self.renderWindow.getLastFPS()

    def RaiseWindow(self):
        try:
            pass
            #stimwin = pygame.display.get_wm_info()['window']
            #self._bci._raise_window(stimwin)
        except:
            pass

    def GetEvents(self):
        #self.keyboard.capture()
        #But we have to check every key
        #self.mouse.capture()
        #This is called on every visual display iteration
        #Return an array of events
        #Each item in the array is passed to myBCPyApplication.Event
        return []

    def DefaultEventHandler(self, event):
        return False
        #return (event.type == pygame.QUIT) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)

    def StartFrame(self, objlist):
        #Called on every visual display iteration
        #objlist is the list of stimuli
        ogre.WindowEventUtilities().messagePump()
        self.root.renderOneFrame()
        time.sleep(.0001)

    def FinishFrame(self):
        pass

    def SetDefaultFont(self, name = None, size = None):
        return SetDefaultFont(name=name, size=size)

    def GetDefaultFont(self):
        return GetDefaultFont()

    @property
    def size(self):
        return (self.width,self.height)

    @property
    def width(self): return self.viewPort.getActualWidth()
    @property
    def height(self): return self.viewPort.getActualHeight()
    def get_size(self): return self.size

    @property
    def bgcolor(self):
        """Color of viewPort.BackgroundColour"""
        return self._bgcolor
    @bgcolor.setter
    def bgcolor(self, value):
        self._bgcolor = value
        self.viewPort.setBackgroundColour(self._bgcolor)
    color=bgcolor

    def Cleanup(self):
        #del self.eventListener
        #=======================================================================
        # self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        # self.inputManager.destroyInputObjectMouse(self.mouse)
        # OIS.InputManager.destroyInputSystem(self.inputManager)
        # self.inputManager = None
        #=======================================================================
        self.root.shutdown()

BciGenericRenderer.subclass = OgreRenderer


class EventListener(ogre.FrameListener, ogre.WindowEventListener, OIS.MouseListener, OIS.KeyListener, OIS.JoyStickListener):
    """
    This class handles all our ogre and OIS events, mouse/keyboard/joystick
    depending on how you initialize this class. All events are handled
    using callbacks (buffered).
    """
    mouse = None
    keyboard = None
    joy = None

    def __init__(self, renderWindow, bufferedMouse, bufferedKeys, bufferedJoy):

        # Initialize the various listener classes we are a subclass from
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        OIS.MouseListener.__init__(self)
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
            if bufferedMouse:
                self.mouse = self.inputManager.createInputObjectMouse(OIS.OISMouse, bufferedMouse)
                self.mouse.setEventCallback(self)

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
        self.delInputObjects()
        OIS.InputManager.destroyInputSystem(self.inputManager)
        self.inputManager = None
        ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)

    def delInputObjects(self):
        # Clean up the initialized input objects
        if self.keyboard:
            self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        if self.mouse:
            self.inputManager.destroyInputObjectMouse(self.mouse)
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
        if self.mouse:
            self.mouse.capture()
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

# Mouse Listener callbacks ###
    def mouseMoved(self, frameEvent):
        return True
    def mousePressed(self, frameEvent, xid):
        return True
    def mouseReleased(self, frameEvent, xid):
        return True

### Key Listener callbacks ###
    def keyPressed(self, evt):
        # Quit the application if we hit the escape button
        if evt.key == OIS.KC_ESCAPE:
            return True
            #self.quitApplication = True
        if evt.key == OIS.KC_1:
            print "hello"
            return True
    def keyReleased(self, evt):
        return True

### Joystick Listener callbacks ###
    def buttonPressed(self, frameEvent, xid):
        return True
    def buttonReleased(self, frameEvent, xid):
        return True
    def axisMoved(self, frameEvent, xid):
        return True

class MeshObject(object):
    """Ogre object"""
    def __init__(self, screen=None, mesh_name='hand.mesh', node=None, position=(0,0,0)):
        """Create a MeshObject. screen is the renderer, node is a parent node, position is where, relative to parent, to place."""
        sm = screen.sceneManager
        self.entity = sm.createEntity(mesh_name + 'Entity', mesh_name)
        node = node if node else sm.getRootSceneNode()
        self.node = node.createChildSceneNode(mesh_name + 'Node', position)
        self.node.attachObject(self.entity)
        #=======================================================================
        # src = self.node.Orientation * (ogre.Vector3().UNIT_Z)
        # directionToGo = ogre.Vector3(0,0,-1)
        # quat = src.getRotationTo(directionToGo)
        # self.node.Orientation=quat
        #=======================================================================

class ImageStimulus(Coords.Box):
    #From shapes
    #ImageStimulus(texture=canvas, size=size, anchor=anchor, position=position, color=color[:3], **kwargs)
    #Where canvas is Image.new("RGBA", csize, (0,0,0,0)) from PIL
    #We need to take the properties of the texture to create an object,
    #then apply the texture
    def __init__(self, content=None, size=None, position=None, anchor='center',
        angle=0.0, color=(1,1,1,1), on=True, texture=None, use_alpha=True, smooth=True, sticky=False, flipx=False, flipy=False):
        Coords.Box.__init__(self)

class Disc(ImageStimulus):
    def __init__(self, position=(10,10), radius=10, size=None, color=(0,0,1), **kwargs):
        ImageStimulus.__init__(self, content=None, size=size, position=position, color=color, **kwargs)

class Block(ImageStimulus):
    #From Meters: rectobj = VisualStimuli.Block(position=barpos, anchor=baranchor, on=True, size=(1,1), color=color)
    def __init__(self, position=(10, 10), size=(10, 10), color=(0, 0, 1), **kwargs):
        ImageStimulus.__init__(self, content=None, **kwargs)

class Text(object):
    """Docstring"""
    def __init__(self, text='Hello world', font_name="BlueHighway",\
                  font_size=16, position=(10,10), color=(1, 1, 1), anchor='lower left', angle=0.0, on=True, smooth=True):
        #Create an overlay
        ovm = ogre.OverlayManager.getSingleton()
        ix = 0
        overlayname = 'Overlay_' + str(ix)
        while ovm.getByName(overlayname):
            ix += 1
            overlayname = 'Overlay_' + str(ix)
        overlay = ovm.create(overlayname)

        #Create a panel
        panel = ovm.createOverlayElement("Panel", 'Panel_' + str(ix))
        panel.setMetricsMode(ogre.GMM_PIXELS)
        panel.setMaterialName("Template/Black50")#BaseWhite #Example/ShadowsOverlay #POCore/Panel

        #Create a text area
        textArea = ovm.createOverlayElement("TextArea", 'TextArea_' + str(ix))
        textArea.setMetricsMode(ogre.GMM_PIXELS)
        textArea.setPosition(0, 0)
        textArea.setVerticalAlignment( ogre.GVA_TOP )

        #Put it together
        overlay.add2D(panel)#Add the panel to the overlay
        panel.addChild(textArea)#Add the text area to the panel

        self.overlay = overlay
        self.panel = panel
        self.textArea = textArea

        #Now update its properties based on input. User property setters where possible.
        self.anchor = anchor
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.size = (len(text)*font_size/(16.0/6),font_size)
        self.position = position
        self.on = on

    #Positional values for the panel
    @property
    def left(self):
        return self.panel.getLeft()
    @left.setter
    def left(self, value):
        self.panel.setLeft(value)
    @property
    def right(self):
        return self.left + self.width
    @right.setter
    def right(self, value):
        self.left = value - self.width
    @property
    def top(self):
        return self.panel.getTop()
    @top.setter
    def top(self, value):
        self.panel.setTop(value)
    @property
    def bottom(self):
        return self.top + self.height
    @bottom.setter
    def bottom(self, value):
        self.panel.setTop(value - self.height)
    @property
    def width(self):
        return self.panel.getWidth()
    @width.setter
    def width(self, value):
        self.panel.setWidth(value)
    @property
    def height(self):
        return self.panel.getHeight()
    @height.setter
    def height(self, value):
        self.panel.setHeight(value)
    @property
    def size(self):
        """Bounding panel size"""
        return (self.width, self.height)
    @size.setter
    def size(self, value):
        self.panel.setDimensions(*value)

    #positional values for the panel's anchor
    @property
    def position(self):
        return Coords.Point([self.x, self.y])
    @position.setter
    def position(self, value):
        pos = Coords.Point(value)
        self.x = pos.x
        self.y = pos.y
    @property
    def x(self):
        return self.right if self.anchor == 'right' else self.left
    @x.setter
    def x(self, value):
        if self.anchor == 'right':
            self.right = value
        else:
            self.left = value
    @property
    def y(self):
        return self.top
    @y.setter
    def y(self, value):
        self.top = value

    @property
    def color(self):
        """Text color"""
        col = self.textArea.getColourTop()
        return (col.r, col.g, col.b, col.a)
    @color.setter
    def color(self, value):
        self.textArea.setColourTop( ogre.ColourValue(*value) )
        self.textArea.setColourBottom( ogre.ColourValue(*value) )

    @property
    def text(self):
        """Text"""
        return self.textArea.getCaption()
    @text.setter
    def text(self, text):
        self.textArea.setCaption(text)

    @property
    def font_size(self):
        """Font Size"""
        return self.textArea.getCharHeight()
    @font_size.setter
    def font_size(self, value):
        self.textArea.setCharHeight(value)

    @property
    def font_name(self):
        """Font Name"""
        return self.textArea.getFontName()
    @font_name.setter
    def font_name(self, value):
        self.textArea.setFontName(value)

    @property
    def on(self):
        """Hidden or not"""
        return self.panel.isVisible()
    @on.setter
    def on(self, value):
        if value: self.overlay.show()
        else: self.overlay.hide()