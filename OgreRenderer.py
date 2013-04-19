#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application
#TODO: ImageStimulus
#TODO: Block
#TODO: Disc
#TODO: Keyboard events passed to application
#TODO: Framerate
#TODO: Fonts

__all__ = ['Text', 'Block', 'Disc', 'ImageStimulus', 'Movie']

#import os
#import sys
import time
#import numpy
import ogre.renderer.OGRE as ogre

import BCPy2000.AppTools.Coords as Coords
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
        self.screen = None
        self._bci = None

    def setup(self, left = None, top = None, width = None, height = None,
        bgcolor = None, framerate = None, changemode = None,
        frameless_window = None, always_on_top = None, title=None,
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
        light.setPosition ( ogre.Vector3(20, 80, -50) )
        light.diffuseColour = 1, 1, 1
        light.specularColour = 1, 1, 1

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
        #This is called on every visual display iteration
        #Return an array of events
        #Each item in the array is passed to myBCPyApplication.Event
        return []

    def DefaultEventHandler(self, event):
        return False

    def StartFrame(self, objlist):
        #Called on every visual display iteration
        #objlist is the list of stimuli
        for obj in objlist: obj.updatePos()
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
        self.root.shutdown()

BciGenericRenderer.subclass = OgreRenderer

class OgreStimulus(Coords.Box):
    """
    Base class for visual stimuli.
    """
    def __init__(self, ogr=None, size=None, position=None, anchor='center', on=True, sticky=False):
        Coords.Box.__init__(self)
        print ogr
        if ogr:
            self.ogr = ogr
        else:
            self.ogr = ogre.Root.getSingleton() #TODO, try to get the OgreRenderer another way

        self._props = {}
        self._last_transformation = None
        if position == None: position = (0,0,0)
        self.anchor = anchor
        self.sticky = False
        self.position = position
        if size: self.size = size
        self.sticky = sticky

    def updatePos(self):
        #=======================================================================
        # From Coords.Box we inherit:
        # self.rect, .lims, .position, .x, .y, .z,
        # .size, .width, .height, .depth, .anchor, .anchorstr,
        # .left, .right, .top, .bottom, .near, .far, .internal
        # These getters and setters operate on internal properties:
        # self.__size, .__position, .__anchor
        # .__anchorstr, .__sticky, .__internal
        # Typically, a BCPy2000 application will operate on its stimuli as follows:
        # my_stim = app.stimuli['my_stim']
        # my_stim.x = 100
        # This does nothing except update the internal variables.
        # For this to be meaningful, we have to use the information in the internal
        # variables to position the object in Ogre.
        #=======================================================================
        pass #This should be defined by the subclasses

class MeshStimulus(OgreStimulus):
    """An OgreStimulus using a provided mesh."""
    def __init__(self, entity=None, mesh_name='hand.mesh', node=None, on=True, **kwargs):
        OgreStimulus.__init__(self, on=on, **kwargs)
        sm = self.ogr.getSceneManager("Default SceneManager")
        if entity is None:
            entity = sm.createEntity(mesh_name + 'Entity', mesh_name)
        self.entity = entity
        node = node if node else sm.getRootSceneNode()
        self.node = node.createChildSceneNode(mesh_name + 'Node', (0,0,0))
        self.node.attachObject(self.entity)
        self.refreshBox()
        self.on = on

    def updatePos(self):
        #TODO: use top-left as 0,0
        self.node.setPosition(-self.x, self.y, self.z)#I don't know why x is in the negative direction.
        if self._last_transformation != self.position:
            self.refreshBox()
            self._last_transformation = self.position

    def refreshBox(self):
        wbox = self.entity.getWorldBoundingBox()
        temp = wbox.getSize()
        self.size = (temp[0], temp[1], temp[2])

    @property
    def on(self):
        """Hidden or not"""
        return self.entity.isVisible()
    @on.setter
    def on(self, value):
        self.entity.setVisible(value)

class ImageStimulus(MeshStimulus):
    """Class for creating 2D-like stimuli.
    Arguments will include content or texture. Use that to make a ManualObject then call the mesh class.
    This class is meant to be laterally-compatible with VisionEggRenderer's ImageStimulus class.
    """
    #http://www.ogre3d.org/tikiwiki/tiki-index.php?page=MadMarx+Tutorial+4&structure=Tutorials
    def __init__(self, content=None, texture=None, color=(1,1,1,1), **kwargs):
        #Create a manual object from content or texture (which are more appropriate for pygame or visionegg)
        #content might be ???
        #texture might be a PIL Image.new("RGBA", csize, (0, 0, 0, 0) )
        #color might have length 3 or 4
        mo = ogre.ManualObject("CubeWithAxes")
        #mo.setDynamic(False)
        cp = 100
        cm = -cp
        mo.begin("BaseWhiteNoLighting", ogre.RenderOperation.OT_TRIANGLE_LIST)
        mo.position(cm, cp, cm)
        mo.colour(ogre.ColourValue(0.0,1.0,0.0,1.0))
        mo.position(cp, cp, cm)
        mo.colour(ogre.ColourValue(1.0,1.0,0.0,1.0));
        mo.position(cp, cm, cm)
        mo.colour(ogre.ColourValue(1.0,0.0,0.0,1.0));
        mo.position(cm, cm, cm)
        mo.colour(ogre.ColourValue(0.0,0.0,0.0,1.0));
        mo.position(cm, cp, cp)
        mo.colour(ogre.ColourValue(0.0,1.0,1.0,1.0));
        mo.position(cp, cp, cp)
        mo.colour(ogre.ColourValue(1.0,1.0,1.0,1.0));
        mo.position(cp, cm, cp)
        mo.colour(ogre.ColourValue(1.0,0.0,1.0,1.0));
        mo.position(cm, cm, cp)
        mo.colour(ogre.ColourValue(0.0,0.0,1.0,1.0));
        mo.triangle(0,1,2)
        mo.triangle(2,3,0)
        mo.triangle(4,6,5)
        mo.triangle(6,4,7)
        mo.triangle(0,4,5)
        mo.triangle(5,1,0)
        mo.triangle(2,6,7)
        mo.triangle(7,3,2)
        mo.triangle(0,7,4)
        mo.triangle(7,0,3)
        mo.triangle(1,5,6)
        mo.triangle(6,2,1)
        mo.end()

        mo.begin("BaseWhiteNoLighting",ogre.RenderOperation.OT_LINE_LIST)
        lAxeSize = 2.0 * cp
        mo.position(0.0, 0.0, 0.0)
        mo.colour(ogre.ColourValue(1,0,0,1))
        mo.position(lAxeSize, 0.0, 0.0)
        mo.colour(ogre.ColourValue(1,0,0,1))
        mo.position(0.0, 0.0, 0.0)
        mo.colour(ogre.ColourValue(0,1,0,1))
        mo.position(0.0, lAxeSize, 0.0)
        mo.colour(ogre.ColourValue(0,1,0,1))
        mo.position(0.0, 0.0, 0.0)
        mo.colour(ogre.ColourValue(0,0,1,1))
        mo.position(0.0, 0.0, lAxeSize)
        mo.colour(ogre.ColourValue(0,0,1,1))
        mo.index(0)
        mo.index(1)
        mo.index(2)
        mo.index(3)
        mo.index(4)
        mo.index(5)
        mo.end()

        lResourceGroup = ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME
        mo.convertToMesh("MeshCubeAndAxe", lResourceGroup)
        MeshStimulus.__init__(self, mesh_name="MeshCubeAndAxe", **kwargs)

#===============================================================================
#        #mo.setRenderQueueGroup(ogre.RenderQueueGroupID.RENDER_QUEUE_OVERLAY)
#        #mo.setUseIdentityProjection(True)
#        #mo.setUseIdentityView(True)
#        #mo.setQueryFlags(0)
#        #mo.clear()
#        #mo.begin("", ogre.RenderOperation.OT_LINE_STRIP) #mat, rendop
#        mo.begin("BaseWhiteNoLighting", ogre.RenderOperation.OT_TRIANGLE_LIST) #mat, rendop Examples/GrassBlades
#
#        for ix in range(len(content)):
#            mo.position(content[ix].x,content[ix].y,content[ix].z)
#            mo.normal(0,0,1)
#            mo.textureCoord(content[ix][0],content[ix][1])
#            mo.colour(color[0],color[1],color[2],color[3])
#        mo.triangle(3,2,1)
#        mo.triangle(1,0,3)
#        #mo.quad(3,2,1,0)
#        mo.end()
#        mo.convertToMesh("moMesh")
#        MeshStimulus.__init__(self, mesh_name="moMesh", **kwargs)
#===============================================================================

    def updatePos(self):
        self.node.setPosition(-self.x, self.y, self.z)#I don't know why x is in the negative direction.

class Disc(ImageStimulus):
    def __init__(self, position=(10,10), radius=10, size=None, color=(0,0,1), **kwargs):
        ogr = ogre.Root.getSingleton()
        sm = ogr.getSceneManager("Default SceneManager")
        entity = sm.createEntity("mySphere",ogre.SceneManager.PT_SPHERE)
        MeshStimulus.__init__(self, entity=entity)

class Block(ImageStimulus):
    """
    Class to create a 2D rectangle.
    http://wiki.python-ogre.org/index.php/Intermediate_Tutorial_4
    """
    #From Meters: rectobj = VisualStimuli.Block(position=barpos, anchor=baranchor, on=True, size=(1,1), color=color)
    def __init__(self, position=(0,0), size=(10, 10), **kwargs):
        #=======================================================================
        # ogr = ogre.Root.getSingleton()
        # renderWindow = ogr.getAutoCreatedWindow()
        # vp = renderWindow.getViewport(0)
        # scrw,scrh = float(vp.getActualWidth()), float(vp.getActualHeight()) #800, 600
        # #sqx = scrw/scrh
        # new_size = (size[0]/scrw, size[1]/scrh)
        # myrect = ogre.Rectangle2D(True)
        # myrect.setCorners(-new_size[0]/2.0,
        #                  new_size[1]/2.0,
        #                  new_size[0]/2.0,
        #                  -new_size[1]/2.0)#l,t,r,b
        # myrect.setMaterial("Template/Black50")
        # myrect.setRenderQueueGroup(ogre.RenderQueueGroupID.RENDER_QUEUE_OVERLAY)
        # MeshStimulus.__init__(self, entity=myrect, **kwargs)
        #=======================================================================
        content = [
                    Coords.Point((position[0]-size[0]/2.0, position[1]-size[1]/2.0)),
                    Coords.Point((position[0]-size[0]/2.0, position[1]+size[1]/2.0)),
                    Coords.Point((position[0]+size[0]/2.0, position[1]+size[1]/2.0)),
                    Coords.Point((position[0]+size[0]/2.0, position[1]-size[1]/2.0))
                ]
        ImageStimulus.__init__(self, content=content, size=size, position=position, **kwargs)


class Movie(ImageStimulus):
    def __init__(self, filename, position=(100,100), size=None, **kwargs):
        pass

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

    def updatePos(self):
        pass
        #Placeholder until this subclasses OgreStimulus
        #Then this will handle the transformation from internal position to onscreen (Ogre) position.

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