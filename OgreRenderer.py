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
        self._props = {}
        self.__filename = None
        self.__original_surface = None
        self.__content_changed = False
        self.__last_transformation = None
        self.__transformed_surface = None
        self.__last_coloring = None
        self.__colored_surface = None
        self.__last_ptr = None
        self.__last_transformed_pos = None
        self.__use_alpha = use_alpha

        if content == None: content = texture
        if content == None:
            if size == None: size = Coords.Size((100,100))
            content = self.default_content(size)

        self.content = content

        if size == None: size = self.original_size

        if position == None: position = (100,100)

        self.anchor = anchor
        self.sticky = False
        self.position = position
        self.size = size
        self.sticky = sticky

        self.color = color
        self.angle = angle
        self.smooth = smooth
        self.flipx = flipx
        self.flipy = flipy
        self.on = on


class Disc(ImageStimulus):
    def __init__(self, position=(10,10), radius=10, size=None, color=(0,0,1), **kwargs):
        if isinstance(radius, (float,int)): radius = (radius,radius)
        if size == None: size = [x * 2 for x in radius]
        if isinstance(size, (float,int)): size = (size,size)
        ImageStimulus.__init__(self, content=None, size=size, position=position, color=color, **kwargs)

    def default_content(self, size):
        size = [max(x,100) for x in size]
        surface = pygame.Surface(size, flags=pygame.SRCALPHA)
        x = int(size[0]/2)
        y = int(size[1]/2)
        pygame.gfxdraw.filled_ellipse(surface, x-1, y-1, x-2, y-2, (255,255,255,255))
        return surface

    @apply
    def radius():
        def fget(self):
            return sum(self.size)/float(len(self.size))
        def fset(self, val):
            if isinstance(val, (float,int)):
                self.size = [min(1,x) for x in self.size]
                prev = sum(self.size)/float(len(self.size))
                self.size *= val/prev
            else:
                self.size = [x*2 for x in val]
        return property(fget, fset, doc="radius of the circle")

class Block(ImageStimulus):
    #From Meters: rectobj = VisualStimuli.Block(position=barpos, anchor=baranchor, on=True, size=(1,1), color=color)
    def __init__(self, position=(10, 10), size=(10, 10), color=(0, 0, 1), **kwargs):
        kwargs.update({'position':position, 'size':size, 'color':color})
        ImageStimulus.__init__(self, content=None, **kwargs)

    def default_content(self, size):
        surface = pygame.Surface(size, flags=pygame.SRCALPHA)
        surface.fill((255,255,255,255))
        return surface

class Movie(ImageStimulus):
    def __init__(self, filename, position=(100,100), size=None, **kwargs):
        self.__movie = m = pygame.movie.Movie(filename)
        if size == None: size = m.get_size()
        if 'use_alpha' not in kwargs: kwargs['use_alpha'] = False
        ImageStimulus.__init__(self, size=size, position=position, **kwargs)
        m.set_display(self._ImageStimulus__original_surface)
        m.render_frame(0)

    def default_content(self, size):
        return pygame.Surface(size, flags=0) # No alpha

    def transform(self, screencoords, force=False):
        self._ImageStimulus__content_changed = True
        return ImageStimulus.transform(self, screencoords=screencoords, force=force)

    def play(self, *pargs, **kwargs): return self.__movie.play(*pargs, **kwargs)
    def stop(self, *pargs, **kwargs): return self.__movie.stop(*pargs, **kwargs)
    def pause(self, *pargs, **kwargs): return self.__movie.pause(*pargs, **kwargs)
    def skip(self, *pargs, **kwargs): return self.__movie.skip(*pargs, **kwargs)
    def rewind(self, *pargs, **kwargs): return self.__movie.rewind(*pargs, **kwargs)
    def render_frame(self, *pargs, **kwargs): return self.__movie.render_frame(*pargs, **kwargs)
    def get_frame(self, *pargs, **kwargs): return self.__movie.get_frame(*pargs, **kwargs)
    def get_time(self, *pargs, **kwargs): return self.__movie.get_time(*pargs, **kwargs)
    def get_busy(self, *pargs, **kwargs): return self.__movie.get_busy(*pargs, **kwargs)
    def get_length(self, *pargs, **kwargs): return self.__movie.get_length(*pargs, **kwargs)
    def has_video(self, *pargs, **kwargs): return self.__movie.has_video(*pargs, **kwargs)
    def has_audio(self, *pargs, **kwargs): return self.__movie.has_audio(*pargs, **kwargs)
    def set_volume(self, *pargs, **kwargs): return self.__movie.set_volume(*pargs, **kwargs)

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

def FindFont(fontnames):
    """
    Tries to find a system font file corresponding to one of the
    supplied list of names. Returns None if no match is found.
    """###
    def matchfont(fontname):
        if fontname.lower().endswith('.ttf'): return fontname
        bold = italic = False
        for i in range(2):
            if fontname.lower().endswith(' italic'): italic = True; fontname = fontname[:-len(' italic')]
            if fontname.lower().endswith(' bold'): bold = True; fontname = fontname[:-len(' bold')]
        return pygame.font.match_font(fontname, bold=int(bold), italic=int(italic))

    if not isinstance(fontnames, (list,tuple)): fontnames = [fontnames]
    fontnames = [f for f in fontnames if f != None]
    f = (filter(None, map(matchfont, fontnames)) + [None])[0]
    if f == None and sys.platform == 'darwin': # pygame on OSX doesn't seem even to try to find fonts...
        f = (filter(os.path.isfile, map(lambda x:os.path.realpath('/Library/Fonts/%s.ttf'%x),fontnames)) + [None])[0]
    return f

def SetDefaultFont(name = None, size = None):
    """
    Set the name and/or size of the font that is used by
    default for Text stimuli. Returns True if the named font
    can be found, False if not.
    """###
    if name != None:
        font = FindFont(name)
        if font == None: return False
        Text.default_font_name = font
    if size != None:
        Text.default_font_size = size
    #pygame.font.Font(Text.default_font_name, Text.default_font_size) # would presumably throw an exception if invalid?
    return True

def GetDefaultFont():
    return Text.default_font_name, Text.default_font_size

#SetDefaultFont(name=pygame.font.get_default_font(), size=20)

def to_surface(src):
    if isinstance(src, pygame.surface.Surface):
        return src
    elif isinstance(src, numpy.ndarray):
        if src.dtype in (numpy.float32, numpy.float64):
            src = src * 255.0 + 0.5
        if src.dtype != numpy.uint8 or not src.flags.carray:
            src = numpy.asarray(src, dtype=numpy.uint8, order='C')
        if src.ndim == 2: src = numpy.expand_dims(src, -1)
        if src.ndim != 3: raise NotImplementedError,"numpy array must be 2- or 3-dimensional"
        if src.shape[2] == 1: src = src.repeat(3, axis=2)
        if src.shape[2] == 3: format = 'RGB'
        elif src.shape[2] == 4: format = 'RGBA'
        else: raise NotImplementedError,"numpy array must be of extent 1, 3 or 4 in the third dimension"
        return pygame.image.fromstring(src.tostring(), (src.shape[1],src.shape[0]), format)
    else:
        return to_surface(to_numpy(src))

def to_numpy(src):
    # Ripped and adapted from VisionEgg.Textures VisionEgg 1.2.1 (c) by Andrew Straw
    if isinstance(src, numpy.ndarray):
        src = numpy.asarray(src)
    elif isinstance(src, pygame.surface.Surface):
        width, height = src.get_size()
        raw_data = pygame.image.tostring(src,'RGBA',1)
        arr = numpy.fromstring( raw_data, dtype=numpy.uint8 ) / 255.0
        arr.shape = (height,width,4)
        return arr[::-1]
    elif hasattr(src, 'tostring'):   # duck-type test for Image.Image
        width, height = src.size

        if src.mode == 'P':
            texel_data=src.convert('RGBA') # convert to RGBA from paletted
            data_format = 6408 # gl.GL_RGBA
        else:
            texel_data = src

        raw_data = texel_data.tostring('raw',texel_data.mode,0,-1)
        if texel_data.mode == 'L':
            shape = (height,width)
        elif texel_data.mode == 'RGB':
            shape = (height,width,3)
        elif texel_data.mode in ('RGBA','RGBX'):
            shape = (height,width,4)
        else:
            raise NotImplementedError('mode %s not supported'%(texel_data.mode,))
        arr = numpy.fromstring( raw_data, dtype=numpy.uint8 )
        arr.shape = shape
        return arr[::-1]
    else:
        raise NotImplementedError("Don't know how to convert texel data %s to numpy array"%(src,))

