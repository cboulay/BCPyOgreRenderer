#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application
#TODO: Fix box and sphere initial loading with wrong size.
#TODO: Window placement
#TODO: Text alternate coordinate frames
#TODO: PolygonTexture
#TODO: Keyboard events passed to application
#TODO: Framerate
#TODO: Fonts
#TODO: Why is right -x?

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
            plugins_path = '.\\BCPyOgreRenderer\\plugins.cfg.nt', resource_path = '.\\BCPyOgreRenderer\\resources.cfg',
            coordinate_mapping = 'pixels from center', **kwds):
        #Set any constants that may come from the parameters.
        #Called during application preflight on the main thread
        self.plugins_path = plugins_path
        self.resource_path = resource_path
        self.__coordinate_mapping = coordinate_mapping

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
        print self.resource_path
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
        self.sceneManager.setAmbientLight(ogre.ColourValue(0.9, 0.9, 0.9))
        #self.sceneManager.setSkyDome(True, 'Examples/CloudySky',4, 8)
        #self.sceneManager.setFog( ogre.FOG_EXP, ogre.ColourValue(1,1,1),0.0005)

        #Create and configure the camera
        self.camera = self.sceneManager.createCamera("Camera")

        #Create and configure the viewPort
        self.viewPort = self.root.getAutoCreatedWindow().addViewport(self.camera)
        self.viewPort.setBackgroundColour(self._bgcolor)

        #Place the camera as far from the 0 plane as the larger of the screen size
        scrw,scrh = self.size
        longd = max(scrw,scrh)
        self.camera.setPosition( ogre.Vector3(0, 0, -longd) )
        self.camera.lookAt( ogre.Vector3(0, 0, 0) )
        self.camera.setNearClipDistance(round(longd/10))

        #Add a light source
        self.light = self.sceneManager.createLight("Light1")
        #light.type = ogre.Light.LT_POINT
        self.light.setPosition ( ogre.Vector3(-scrw, scrh, -longd/5.0) )
        self.light.diffuseColour = 0.5, 0.5, 0.5
        self.light.specularColour = 0.3, 0.3, 0.3

        self.coordinate_mapping = self.__coordinate_mapping

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
        #for obj in objlist: obj.updatePos()
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
    def get_size(self): return self.size
    @property
    def width(self): return self.viewPort.getActualWidth()
    @property
    def height(self): return self.viewPort.getActualHeight()

    @property
    def bgcolor(self):
        """Color of viewPort.BackgroundColour"""
        return self._bgcolor
    @bgcolor.setter
    def bgcolor(self, value):
        self._bgcolor = value
        self.viewPort.setBackgroundColour(self._bgcolor)
    color=bgcolor

    @property
    def coordinate_mapping(self):
        return self.__coordinate_mapping
    @coordinate_mapping.setter
    def coordinate_mapping(self, value):
        zpos = self.camera.getPosition()[2]
        cm = value.lower().replace('bottom', 'lower').replace('top', 'upper').replace(' ', '')
        scrw,scrh = self.size
        longd = max((scrw,scrh))
        if cm == 'pixelsfromlowerleft': #VisionEgg default
            self.camera.setPosition( ogre.Vector3(-scrw/2, scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, scrh/2 + 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(-scrw, scrh, -longd) )
        elif cm == 'pixelsfromupperleft': #PygameRenderer default
            self.camera.setPosition( ogre.Vector3(-scrw/2, -scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, -scrh/2 + 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(-scrw, -scrh, -longd) )
        elif cm == 'pixelsfromcenter': #OgreRenderer default
            self.camera.setPosition( ogre.Vector3(0, 0, zpos) )
            #self.light.setPosition ( ogre.Vector3(20, 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(-scrw/2, scrh/2, -longd/5.0) )
        else:
            raise ValueError('coordinate_mapping "%s" is unsupported' % value)
        self.__coordinate_mapping = value

    def Cleanup(self):
        #del self.eventListener
        self.root.shutdown()

BciGenericRenderer.subclass = OgreRenderer

class EntityStimulus(Coords.Box):
    """Creates a 3D Ogre object using provided mesh or entity.
    """
    def __init__(self, mesh_name='hand.mesh', entity=None, parent=None,
                 size=(1,1,1), color=(1,1,1,1), position=(0,0,0), anchor='center', on=True, sticky=False,
                 **kwargs):
        Coords.Box.__init__(self)
        self.ogr = ogre.Root.getSingleton()
        self.sceneManager = self.ogr.getSceneManager("Default SceneManager")
        self.entity = entity if entity else self.sceneManager.createEntity(mesh_name + 'Entity', mesh_name)
        parent = parent if parent else self.sceneManager.getRootSceneNode()
        self.node = parent.createChildSceneNode(self.entity.getName() + 'Node', (0,0,0))
        self.node.attachObject(self.entity)

        #Set desired anchor, position, and size then reset
        super(EntityStimulus, self.__class__).anchor.fset(self, anchor)
        super(EntityStimulus, self.__class__).position.fset(self, position)
        self.sticky = sticky#This doesn't affect anything so we can use the direct access
        self.size = size#This will cause the reset
        self.color = color
        self.on = on

    #size, width, height, depth
    def reset(self):
        desiredSize = super(EntityStimulus, self).size
        anch = super(EntityStimulus, self).anchor
        desiredAnchPos = super(EntityStimulus, self).position
        #Account for negative sizes
        negDim = [x<0 for x in desiredSize]
        desiredSize = [-siz if neg else siz for siz,neg in zip(desiredSize,negDim)]
        desiredSize = Coords.Size([siz if siz>0 else 1.0 for siz in desiredSize])#Make sure we never try to set size to 0
        #Scale
        self.node.setScale(desiredSize[0],desiredSize[1],desiredSize[2])
        #Position
        anch = [-1*a if neg else a for a,neg in zip(anch,negDim)]#Reposition the anchor if we have any negative sizes
        desiredNodePos = desiredAnchPos - anch*desiredSize/2#Unadjust the anchor position to get node position
        self.node.setPosition(-desiredNodePos[0],desiredNodePos[1],desiredNodePos[2])

    @property
    def size(self):
        wbox = self.entity.getWorldBoundingBox()
        trueSize = wbox.getSize()
        trueSize = (trueSize[0], trueSize[1], trueSize[2])#Convert from Ogre to tuple
        #trueSize = [ts if ts else 1.0 for ts in trueSize]#Replace 0's with 1's on recently instantiated objects
        super(EntityStimulus, self.__class__).size.fset(self, trueSize)
        return super(EntityStimulus, self).size
    @size.setter
    def size(self, value):
        value = tuple(value)
        while len(value)<3: value = value + (None,) #Fill out til it's 3D
        value = tuple([x if x and x!=0 else 1.0 for x in value])#Replace 0/None's with 1's
        super(EntityStimulus, self.__class__).size.fset(self, value)
        self.reset()
    @property
    def width(self):
        return self.size.x #Returns updated representation
    @width.setter
    def width(self, value):
        super(EntityStimulus, self.__class__).width.fset(self, value)
        self.reset()
    @property
    def height(self):
        return self.size.y
    @height.setter
    def height(self, value):
        super(EntityStimulus, self.__class__).height.fset(self, value)
        self.reset()
    @property
    def depth(self):
        return self.size.z
    @depth.setter
    def depth(self, value):
        super(EntityStimulus, self.__class__).depth.fset(self, value)
        self.reset()

    #position, x, y, z
    @property
    def position(self):
        nodePos = self.node.getPosition() #Get the true position
        nodePos = Coords.Point([-nodePos[0], nodePos[1], nodePos[2]]) #Convert to screen coordinates
        anchorPos = nodePos+self.anchor*self.size/2 #Adjust for the anchor
        super(EntityStimulus, self.__class__).position.fset(self, anchorPos) #Save internally
        return super(EntityStimulus, self).position
    @position.setter
    def position(self, value):
        #Account for None in value
        currAnchPos = self.position
        newAnchPos = [new if new else old for new,old in zip(value,currAnchPos)]
        super(EntityStimulus, self.__class__).position.fset(self, newAnchPos)
        self.reset()
    @property
    def x(self):
        return self.position.x #This updates __position with the true position.
    @x.setter
    def x(self, value):
        super(EntityStimulus, self.__class__).x.fset(self, value)
        self.reset()
    @property
    def y(self):
        return self.position.y #This updates __position with the true position.
    @y.setter
    def y(self, value):
        super(EntityStimulus, self.__class__).y.fset(self, value)
        self.reset()
    @property
    def z(self):
        return self.position.z #This updates __position with the true position.
    @z.setter
    def z(self, value):
        super(EntityStimulus, self.__class__).z.fset(self, value)
        self.reset()

    @property
    def anchor(self):
        return super(EntityStimulus, self).anchor
    @anchor.setter
    def anchor(self, value):
        super(EntityStimulus, self.__class__).anchor.fset(self, value)
        self.reset()

    @property
    def on(self):
        """Hidden or not"""
        return self.entity.isVisible()
    @on.setter
    def on(self, value):
        self.entity.setVisible(value)

    @property
    def color(self):
        """Color"""
        return self.__color
    @color.setter
    def color(self, value):
        #Might not have much of an effect depending on material type
        value = tuple(value)
        if len(value)<4: value = value + (1.0,)
        r,g,b,a = float(value[0]), float(value[1]), float(value[2]), float(value[3])
        nsubs = self.entity.getNumSubEntities()
        for se_ix in range(nsubs):
            se = self.entity.getSubEntity(se_ix)
            mat = se.getMaterial()
            mat.setAmbient(r,g,b)
            mat.setDiffuse(r,g,b,a)
            mat.setSpecular(r,g,b,a)
            mat.setSelfIllumination(r,g,b)
        self.__color = value

    def makeMaterialUnique(self, entity):
        nsubs = entity.getNumSubEntities()
        matMgr = ogre.MaterialManager.getSingleton()
        for se_ix in range(nsubs):
            se = entity.getSubEntity(se_ix)
            matName = se.getMaterialName()
            mat = se.getMaterial()
            uqname = matName + "_" + entity.getName()
            if matMgr.resourceExists(uqname):
                newmat = matMgr.getByName(uqname)
            else:
                newmat = mat.clone(uqname)
                #The only reason we'd use this function is to change
                #the material's color/alpha, so let's enable that
                newmat.setDepthWriteEnabled(False)
                newmat.setSceneBlending(ogre.SceneBlendType.SBT_TRANSPARENT_ALPHA)
            se.setMaterial(newmat)

class HandStimulus(EntityStimulus):
    def __init__(self, mesh_name='hand.mesh', n_poses=100, **kwargs):
        EntityStimulus.__init__(self, mesh_name='hand.mesh', **kwargs)
        self.scale(80.0)
        import math
        self.node.roll(-1.1*math.pi/2)
        self.node.pitch(-1.1*math.pi/2)
        self.importPoses(n_poses)
        self.setPose(0)

    def importPoses(self, n_poses=100):
        import json
        pfile = open('media/libhand/poses/stop_it.json')
        extended_rot = json.load(pfile)
        extended_rot = extended_rot["hand_joints"]
        pfile.close()
        #extended_rot are joint angles to apply to the default position

        #Get the starting orientation in quaternions
        skel = self.entity.getSkeleton()
        starting_q = {}
        for key in extended_rot:
            bone = skel.getBone(key)
            starting_q[key] = bone.getOrientation()
            bone.setManuallyControlled(True)

        #Get the iterated orientation in quaternions
        self.poses = []
        for ix in range(n_poses+1):
            pose_i = {}
            for key in extended_rot:
                #Reset the bone
                bone = skel.getBone(key)
                bone.setOrientation(starting_q[key])
                #Rotate the bone and save its new orientation
                interp_rot = [p*ix/n_poses for p in extended_rot[key]] #Starting is 0 so it's OK
                m = ogre.Matrix3()
                m.FromEulerAnglesXYZ(interp_rot[0], interp_rot[1], interp_rot[2])
                q = ogre.Quaternion(m)
                bone.rotate(q)
                pose_i[key] = bone.getOrientation()
            self.poses.append(pose_i)

    def setPose(self, pose_ix):
        skel = self.entity.getSkeleton()
        pose = self.poses[pose_ix]
        for key in pose: #key = "finger4joint2"
            bone = skel.getBone(key)
            bone.setOrientation(pose[key])

class PrefabStimulus(EntityStimulus):
    def __init__(self, pttype="sphere", **kwargs):
        ogr = ogre.Root.getSingleton()
        sceneManager = ogr.getSceneManager("Default SceneManager")
        myix = 0
        while sceneManager.hasEntity(pttype + "_" + str(myix)):
            myix += 1
        if pttype == "sphere":
            entity = sceneManager.createEntity(pttype + "_" + str(myix), ogre.SceneManager.PT_SPHERE)
        elif pttype == "cube":
            entity = sceneManager.createEntity(pttype + "_" + str(myix), ogre.SceneManager.PT_CUBE)
        self.makeMaterialUnique(entity)
        EntityStimulus.__init__(self, entity=entity, **kwargs)

class Disc(PrefabStimulus):
    """ Class to create a 3D Sphere."""
    def __init__(self, radius=10, **kwargs):
        #kwargs['size'] = (2*radius,2*radius,2*radius)
        PrefabStimulus.__init__(self, pttype="sphere", **kwargs)
        self.radius = radius

    @property
    def radius(self):
        """Sphere radius."""
        return self.width/2.0
    @radius.setter
    def radius(self, value):
        self.size = (value*2.0, value*2.0, value*2.0)

class Block(PrefabStimulus):
    """
    Class to create a 3D cube.
    """
    #From Meters: rectobj = VisualStimuli.Block(position=barpos, anchor=baranchor, on=True, size=(1,1), color=color)
    def __init__(self, size=(10,10,10), **kwargs):
        #kwargs['size'] = (1,1,1) #Will init with default size of 102,102,102
        PrefabStimulus.__init__(self, pttype="cube", **kwargs)
        self.size = size

class ImageStimulus(EntityStimulus):
    """Class for creating 2D-like stimuli.
    Arguments will include content or texture. Use that to make a ManualObject then call the mesh class.
    This class is meant to be laterally-compatible with VisionEggRenderer's ImageStimulus class.
    """
    #http://www.ogre3d.org/tikiwiki/tiki-index.php?page=MadMarx+Tutorial+4&structure=Tutorials
    #http://wiki.python-ogre.org/index.php/Intermediate_Tutorial_4
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
        EntityStimulus.__init__(self, mesh_name="MeshCubeAndAxe", **kwargs)

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
        #self.font_name = font_name #TODO: Fonts!
        self.font_name = "BlueHighway"
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