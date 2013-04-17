#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application

__all__ = ['Text', 'Block', 'Disc', 'ImageStimulus', 'Movie']

import os
import sys
import time
import numpy
import pygame #For event monitoring
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
        self.plugins_path = 'plugins.cfg.nt'
        self.resource_path = 'resources.cfg'

    def setup(self, left = None, top = None, width = None, height = None,
        bgcolor = None, framerate = None, changemode = None,
        frameless_window = None, always_on_top = None, title=None,
        coordinate_mapping = None,
        **kwds):
        #Set any constants that may come from the parameters.
        #Called during application preflight on the main thread
        pass

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
        self.createFrameListener()

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
        self.root.initialise(True, "Tutorial Render Window")
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
        self.sceneManager.setSkyDome(True, 'Examples/CloudySky',4, 8)
        self.sceneManager.setFog( ogre.FOG_EXP, ogre.ColourValue(1,1,1),0.0002)

        #Create and configure the camera
        self.camera = self.sceneManager.createCamera("Camera")
        self.camera.setPosition( ogre.Vector3(0, 100, -400) )
        self.camera.lookAt( ogre.Vector3(0, 25, 1) )
        self.camera.setNearClipDistance(15)

        #Create and configure the viewPort
        self.viewPort = self.root.getAutoCreatedWindow().addViewport(self.camera)
        self.viewPort.setBackgroundColour(self._bgcolor)

        #Add a light source
        light = self.sceneManager.createLight("Light1")
        #light.type = ogre.Light.LT_POINT
        light.position = 20, 80, 50 #light.setPosition ( ogre.Vector3(20, 80, 50) )
        #light.diffuseColour = 1, 1, 1
        #light.specularColour = 1, 1, 1

        #Add an entity
        self.entityHand = self.sceneManager.createEntity("Hand", "hand.mesh")
        self.nodeHand = self.sceneManager.getRootSceneNode().createChildSceneNode("HandNode")
        self.nodeHand.attachObject(self.entityHand)
        self.nodeHand.setScale(50,50,50)
        #Try something like self.nodeHand.yaw(.2) while the app is running

    def createFrameListener(self):
        self.eventListener = EventListener(self.renderWindow, True, True, False) # switch the final "False" into "True" to get joystick support
        self.root.addFrameListener(self.eventListener)

    def GetFrameRate(self):
        return self.framerate  # TODO: not the real framerate

    def RaiseWindow(self):
        try:
            pass
            #stimwin = pygame.display.get_wm_info()['window']
            #self._bci._raise_window(stimwin)
        except:
            pass

    def GetEvents(self):
        #This is called on every visual display iteration
        #Return an array of events
        #Each item in the array is passed to myBCPyApplication.Event
        #TODO: Move the keyboard/mouse/joystick capture from EventListener to here.
        return []
        #return pygame.event.get()

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
        return (0,0)

    @property
    def width(self): return self.size[0]
    @property
    def height(self): return self.size[1]
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
        del self.eventListener
        self.root.shutdown()
        #=======================================================================
        # self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        # self.inputManager.destroyInputObjectMouse(self.mouse)
        # OIS.InputManager.destroyInputSystem(self.inputManager)
        # self.inputManager = None
        #=======================================================================

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

class UberSpinningNinja(object):
    """Create a ninja!"""
    def __init__(self, app, node, start_coords):
        self.entity = app.sm.createEntity('ninja', 'ninja.mesh')
        self.node = node.createChildSceneNode("ninja_node", start_coords)
        self.node.attachObject(self.entity)
        #self.node.setScale(50,50,50)

        src = self.node.Orientation * (ogre.Vector3().UNIT_Z)
        directionToGo = ogre.Vector3(0,0,-1)
        quat = src.getRotationTo(directionToGo)
        self.node.Orientation=quat

        self.spinning_x = 0 # 1 for clockwise, -1 for counter clockwise

    def start_spinning(self, clock_wise=1):
        self.spinning_x = clock_wise

    def stop_spinning(self):
        self.spinning_x = 0

    def update(self):
        self.node.yaw(.002 * self.spinning_x)

class ImageStimulus(Coords.Box):
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

    def default_content(self, size):
        return pygame.Surface(size, flags=pygame.SRCALPHA)


    def transform(self, screencoords=None, force=False):
        p = self._props
        srcsize  = tuple([int(round(x)) for x in self.original_size])
        dstsize  = tuple([int(round(x)) for x in self.size])
        angle = float(p['angle']) % 360.0
        smooth = bool(p['smooth'])
        changed = bool(self.__content_changed)
        flipx = bool(p['flipx'])
        flipy = bool(p['flipy'])
        color = tuple(p['color'])
        if len(color) == 3: color = color + (1.0,)
        athresh = 0.2 # degrees
        pos = Coords.Point((self.left, self.top))
        origin = pos

        origin = Coords.Point(self.anchor.through(self))
        if screencoords != None:
            pos     = screencoords.int2ext(pos, 'position')
            origin  = screencoords.int2ext(origin, 'position')
            #dstsize = tuple([abs(x) for x in screencoords.int2ext(dstsize, 'size')])   # for now, let's express size as an absolute size in pixels even if position coords are on some other scale
            # TODO: the previous couple of lines seem to use up a lot of CPU...

        # now we're working in pixels from top left
        ptr = (tuple(pos),tuple(origin),tuple(dstsize),angle)
        if ptr == self.__last_ptr:
            pos = self.__last_transformed_pos
        else:
            r = numpy.exp(-1.0j * angle * numpy.pi/180.0)
            def rotate(p, r, origin):
                p = p - origin
                c = (float(p[0]) + p[1]*1.0j) * r
                p[:] = c.real,c.imag
                p = p + origin
                return p
            w,h = dstsize
            corners = [rotate(pos+x, r, origin) for x in [(0,0),(0,h),(w,h),(w,0)]]
            #print "pos =",pos
            #print "origin =",origin
            #print "corners =",corners
            x,y = zip(*corners)
            pos[:] = min(x),min(y)
            #print "transformed_pos =",pos
            #print
            self.__last_ptr = ptr
            self.__last_transformed_pos = pos

        tr = (tuple(srcsize),tuple(dstsize),angle,flipx,flipy,smooth)
        if force or changed or tr != self.__last_transformation:
            t = self.__original_surface
            if flipx or flipy: t = pygame.transform.flip(t, flipx, flipy)
            if smooth:
                scaling = [float(dstsize[i]) / float(srcsize[i]) for i in (0,1)]
                proportional = (abs(scaling[0]-scaling[1]) < 1e-2)
                if dstsize != srcsize and not proportional: t = pygame.transform.smoothscale(t, dstsize)
                elif  dstsize != srcsize  and proportional: t = pygame.transform.rotozoom(t, angle, scaling[0])
                elif  abs(angle) > athresh:				 t = pygame.transform.rotozoom(t, angle, 1.0)
            else:
                if dstsize != srcsize: t = pygame.transform.scale(t, dstsize)
                if abs(angle) > athresh:   t = pygame.transform.rotate(t, -angle)
            self.__colored_surface = self.__transformed_surface = t
            changed = True
        self.__last_transformation = tr
        if force or changed or color != self.__last_coloring:
            t = self.__transformed_surface
            if color != (1.0,1.0,1.0,1.0):
                t = to_numpy(t)
                a = numpy.array(color[:t.shape[2]])
                a.shape = (1,1,a.size)
                t = to_surface(t * a)
            self.__colored_surface = t
        self.__last_coloring = color
        self.__content_changed = False
        return self.__colored_surface, pos

    def draw(self, screen, screencoords):
        if not self._props['on']: return
        t, pos = self.transform(screencoords=screencoords)
        screen.blit(t, pos)

    @apply
    def original_size():
        def fget(self):
            orig = self.__original_surface
            if orig == None: return None
            return Coords.Size((orig.get_width(), orig.get_height()))
        return property(fget, doc="the width and height of the original image (read only)")

    @apply
    def content():
        def fget(self):
            return to_numpy(self.__original_surface)
        def fset(self, val):
            if isinstance(val, basestring):
                val = pygame.image.load(val)
                self.__filename = val
            else:
                val = to_surface(val)
            if self.__use_alpha: val = val.convert_alpha()
            elif val.get_flags() & pygame.SRCALPHA: val = val.convert()
            self.__original_surface = val
            self.__content_changed = True
        return property(fget, fset, doc='the content of the image stimulus as a numpy array')

    @apply
    def color():
        def fget(self):  p = self._props; return p['color']
        def fset(self, val):
            p = self._props;
            try: val = [float(x) for x in val]
            except: raise ValueError('invalid color specification')
            if len(val) not in [3,4]: raise ValueError('color specification should have 3 or 4 elements')
            p['color'] = val
        return property(fget, fset, doc='3- or 4-element sequence denoting RGB or RGBA colour')

    @apply
    def angle():
        def fget(self):  p = self._props; return p['angle']
        def fset(self, val):
            try: val = float(val)
            except: raise TypeError('angle should be a floating-point scalar')
            p = self._props;
            p['angle'] = val % 360.0
        return property(fget, fset, doc='rotation angle in degrees')

    @apply
    def smooth():
        def fget(self):  p = self._props; return p['smooth']
        def fset(self, val):
            try: val = bool(val)
            except: raise TypeError('smooth should be a boolean')
            p = self._props;
            p['smooth'] = val
        return property(fget, fset, doc='whether or not pygame transformations are smooth')

    @apply
    def on():
        def fget(self):  p = self._props; return p['on']
        def fset(self, val):
            try: val = bool(val)
            except: raise TypeError('on should be a boolean')
            p = self._props;
            p['on'] = val
        return property(fget, fset, doc='whether or not the stimulus is displayed')

    @apply
    def flipx():
        def fget(self):  p = self._props; return p['flipx']
        def fset(self, val):
            try: val = bool(val)
            except: raise TypeError('flipx should be a boolean')
            p = self._props;
            p['flipx'] = val
        return property(fget, fset, doc='whether to display image flipped left-to-right')

    @apply
    def flipy():
        def fget(self):  p = self._props; return p['flipy']
        def fset(self, val):
            try: val = bool(val)
            except: raise TypeError('flipy should be a boolean')
            p = self._props;
            p['flipy'] = val
        return property(fget, fset, doc='whether to display image flipped top-to-bottom')

#size=None, position=None, anchor='center',
#angle=0.0, color=(1,1,1,1), on=True, texture=None, use_alpha=True, smooth=True, sticky=False, flipx=False, flipy=False):

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

#class Text(ImageStimulus):

class Text():
    """Docstring"""
    def __init__(self, text='Hello world', font_name=None, font_size=None, position=(10,10), color=(1, 1, 1), anchor='lower left', angle=0.0, on=True, smooth=True):
        #Create an overlay
        ovm = ogre.OverlayManager.getSingleton()
        overlay = ov = ovm.create("OverlayName")

        #Create a panel
        panel = ovm.createOverlayElement("Panel", "PanelName")
        #panel.setPosition(x,y)
        #panel.setDimensions(x,y)
        #panel.setMaterialName("MaterialName")

        #Create a text area
        textArea = ovm.createOverlayElement("TextArea", "TextAreaName")
        #textArea.setPosition(0, 0)
        #textArea.setDimensions(100, 100)
        #textArea.setCaption("Hello, World!")
        #textArea.setCharHeight(16)
        #textArea.setFontName("TrebuchetMSBold")
        #textArea.setColourBottom(0.3, 0.5, 0.3)
        #textArea.setColourTop(0.5, 0.5, 0.5)

        #Put it together
        panel.addChild(textArea)#Add the text area to the panel
        overlay.add2D(panel)#Add the panel to the overlay
        overlay.show()#Show the overlay

    def transform(self, screencoords, force=False):
        p = self._props
        if self.__font_changed:
            fn = FindFont(p['font_name'])
            if fn != None: self.__font_object = pygame.font.Font(fn, p['font_size'])
            self.__font_changed = False
            self.__text_changed = True
        if self.__text_changed:
            t = str(p['text'])
            if p['value'] != None:
                val = p['value']
                if isinstance(val, list): val = tuple(val)
                try: t = t % val
                except: pass
            orig = self.__font_object.render(t, True, (255,255,255)) # TODO: multiline text....
            self.__text_changed = False
            self.size = Coords.Size((orig.get_width(), orig.get_height()))
            self.content = orig
        return ImageStimulus.transform(self, screencoords=screencoords, force=force)

    @apply
    def value():
        def fget(self):  p = self._props; return p['value']
        def fset(self, val):
            if isinstance(val, (tuple,list,numpy.ndarray)): val = list(val)
            p = self._props;
            self.__text_changed = p['value'] != val
            p['value'] = val
        return property(fget, fset, doc='optional list of values for interpolation into text')

    @apply
    def text():
        def fget(self):  p = self._props; return p['text']
        def fset(self, val):
            if val == None or val == '': val = ' '
            p = self._props;
            self.__text_changed = p['text'] != val
            p['text'] = val
        return property(fget, fset, doc='text content')

    @apply
    def font_name():
        def fget(self):  p = self._props; return p['font_name']
        def fset(self, val):
            p = self._props;
            self.__font_changed = p['font_name'] != val
            p['font_name'] = val
        return property(fget, fset, doc='font name')

    @apply
    def font_size():
        def fget(self):  p = self._props; return p['font_size']
        def fset(self, val):
            p = self._props;
            self.__font_changed = p['font_size'] != val
            p['font_size'] = val
        return property(fget, fset, doc='font size')

    def _getAttributeNames(self):
        return self._props.keys()

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

SetDefaultFont(name=pygame.font.get_default_font(), size=20)

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

