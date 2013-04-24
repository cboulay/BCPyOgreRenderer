#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application
#TODO: Text alternate coordinate frames
#TODO: PolygonTexture->ImageStimulus
#TODO: Keyboard events passed to application
#TODO: Fonts
#TODO: Window placement. Removing the border causes unexpected placement

__all__ = ['Text', 'Block', 'Disc', 'ImageStimulus', 'Movie']

import sys
import os
import os.path
import time
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import BCPy2000.AppTools.Coords as Coords
try:    from BCI2000PythonApplication    import BciGenericRenderer, BciStimulus   # development copy
except: from BCPy2000.GenericApplication import BciGenericRenderer, BciStimulus   # installed copy

class OgreRenderer(BciGenericRenderer):
    debugText=""
    def __init__(self):
        #Set some defaults that aren't defined by setup (i.e. non-parameterizable constants)
        self.framerate = 60.#Checking the framerate is too slow.
        self.screen = None
        self._bci = None
        self._bci_stepping = True

    def __del__(self):
        "Clear variables, this should not actually be needed."
        del self.camera
        del self.sceneManager
        del self.frameListener
        #if self.world:
            #del self.world
        del self.root
        del self.renderWindow

    def setup(self, width = 800, height = 600, left = 0, top = 0,
            bgcolor = (0.5, 0.5, 0.5), frameless_window = None, title="BCPyOgre",
            plugins_path = '.\\BCPyOgreRenderer\\plugins.cfg.nt', resource_path = '.\\BCPyOgreRenderer\\resources.cfg',
            coordinate_mapping = 'pixels from center', id=None, scale=None, **kwds):
        """BCI2000 parameters relevant to the display are passed in here,
        durin gthe Application Preflight, either directly or through AppTools.Displays.fullscreen
        """
        self._coords = Coords.Box(left=left, top=top, width=width, height=height, sticky=True, anchor='top left')
        self._bgcolor = bgcolor
        self._plugins_path = plugins_path
        self._resource_path = resource_path
        self._coordinate_mapping = coordinate_mapping
        self._screen_id = id #Might be None. This might be -1, so we need to find out how many monitors we have after ogre is initialized
        self._screen_scale = scale #Might be None. This may overwrite width and height below after ogre is initialized
        self._screen_params = {
                                "title": title,
                                "border": "none" if frameless_window else "fixed",#"none","fixed","resize"
                                "left": left,
                                "top": top,
                                "monitorIndex": self._screen_id
                                }

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
        #self.setupInputSystem()
        #self.startRenderLoop()

    # The Root constructor for the ogre
    def createRoot(self):
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
        #self.root.initialise(True, self._screen_params["title"])
        #self.renderWindow = self.root.getAutoCreatedWindow()
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
        #misc["border"] = self._screen_params["border"]
        misc["left"] = str(int(self._screen_params["left"]))
        misc["top"] = str(int(self._screen_params["top"]))
        #misc["monitorIndex"] = str(int(self._screen_params["monitorIndex"]))#Doesn't seem to work :(
        if self._screen_scale:
            pass
            #TODO: Get the size of the monitor and scale if a scale is provided
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
        self.viewPort.setBackgroundColour(self._bgcolor)

        #Place the camera as far from the 0 plane as the larger of the screen size
        scrw,scrh = self.size
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

        self.coordinate_mapping = self._coordinate_mapping

    def createFrameListener(self):
        """Creates the FrameListener."""
        #,self.frameListener, self.frameListener.Mouse
        self.frameListener = FrameListener(self.renderWindow, self.camera)
        #self.frameListener.unittest = self.unittest
        self.frameListener.showDebugOverlay(True)
        self.root.addFrameListener(self.frameListener)

    def startRenderLoop(self):
        self.root.startRendering()

#===============================================================================
#    def cleanUp(self):
#        # Clean up CEGUI
#        print "CLEANING"
#        #del self.renderer
#        del self.system
#
#        # Clean up Ogre
#        #del self.exitListener
#        del self.root
#===============================================================================

    def GetFrameRate(self):
        if 'FramesPerSecond' in self._bci.estimated:
            return self._bci.estimated['FramesPerSecond']['running']#self.renderWindow.getLastFPS() is too slow to do every frame.
        else: return self.framerate

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
        if self._bci_stepping:
            ogre.WindowEventUtilities().messagePump()
            if not self.root.renderOneFrame():
               raise NotImplementedError,"TODO: Use a better error to indicate rendering failed."
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
        return self._coordinate_mapping
    @coordinate_mapping.setter
    def coordinate_mapping(self, value):
        zpos = self.camera.getPosition()[2]
        cm = value.lower().replace('bottom', 'lower').replace('top', 'upper').replace(' ', '')
        scrw,scrh = self.size
        longd = max((scrw,scrh))
        if cm == 'pixelsfromlowerleft': #VisionEgg default
            self.camera.setPosition( ogre.Vector3(scrw/2, scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, scrh/2 + 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(scrw, scrh, longd) )
        elif cm == 'pixelsfromupperleft': #PygameRenderer default
            self.camera.setPosition( ogre.Vector3(scrw/2, -scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, -scrh/2 + 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(scrw, -scrh, longd) )
        elif cm == 'pixelsfromcenter': #OgreRenderer default
            self.camera.setPosition( ogre.Vector3(0, 0, zpos) )
            #self.light.setPosition ( ogre.Vector3(20, 80, -longd/10.0) )
            self.light.setPosition ( ogre.Vector3(scrw/2, scrh/2, longd/5.0) )
        else:
            raise ValueError('coordinate_mapping "%s" is unsupported' % value)
        self._coordinate_mapping = value

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
        orig_size = self.entity.getBoundingBox().getSize()
        self.__original_size = Coords.Size((orig_size[0],orig_size[1],orig_size[2]))
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
        origSize = self.__original_size
        desiredScale = desiredSize/origSize
        self.node.setScale(desiredScale[0],desiredScale[1],desiredScale[2])
        #Position
        anch = [-1*a if neg else a for a,neg in zip(anch,negDim)]#Reposition the anchor if we have any negative sizes
        desiredNodePos = desiredAnchPos - anch*desiredSize/2#Unadjust the anchor position to get node position
        self.node.setPosition(desiredNodePos[0],desiredNodePos[1],desiredNodePos[2])

    @property
    def size(self):
        trueSize = self.entity.getWorldBoundingBox().getSize()
        trueSize = (trueSize[0], trueSize[1], trueSize[2])#Convert from Ogre to tuple
        if trueSize[0]==0 and trueSize[1]==0 and trueSize[2]==0: #Not yet in the world.
            trueSize = self.__original_size
        super(EntityStimulus, self.__class__).size.fset(self, trueSize)
        return super(EntityStimulus, self).size
    @size.setter
    def size(self, value):
        value = tuple(value)
        while len(value)<3: value = value + (None,) #Fill out til it's 3D
        value = tuple([x if x else 1.0 for x in value])#Replace None's with 1's
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
    def scale(self, value):
        if not isinstance(value, (tuple,list)): value = tuple([value])
        while len(value)<3: value = value + (value[-1], )
        self.size = self.size * value

    #position, x, y, z
    @property
    def position(self):
        nodePos = self.node.getPosition() #Get the true position
        nodePos = Coords.Point([nodePos[0], nodePos[1], nodePos[2]]) #Convert to screen coordinates
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
        matMgr = ogre.MaterialManager.getSingleton()
        nsubs = entity.getNumSubEntities()
        for se_ix in range(nsubs):
            se = entity.getSubEntity(se_ix)
            matName = se.getMaterialName()
            mat = se.getMaterial()
            uqname = matName + "_" + entity.getName()
            if matMgr.resourceExists(uqname):
                newmat = matMgr.getByName(uqname)
            else:
                newmat = mat.clone(uqname)
                #The only reason we'd use this function is to later change
                #the material's color/alpha, so let's enable that functionality
                newmat.setDepthWriteEnabled(False)
                newmat.setSceneBlending(ogre.SceneBlendType.SBT_TRANSPARENT_ALPHA)
            se.setMaterial(newmat)

class HandStimulus(EntityStimulus):
    def __init__(self, mesh_name='hand.mesh', n_poses=100, **kwargs):
        EntityStimulus.__init__(self, mesh_name='hand.mesh', **kwargs)
        #The Hand's bounding box is not indicative of its size.
        self._EntityStimulus__original_size = Coords.Size((1.5189208984375, 1.2220458984375, 1.366025447845459))
        #self.size = self._EntityStimulus__original_size * 80
        self.scale(80)
        import math
        self.node.roll(-80*math.pi/180)
        self.node.pitch(60*math.pi/180)
        self.importPoses(n_poses)
        self.setPose(0)

    def importPoses(self, n_poses=100):
        import json
        pfile = open('media/libhand/poses/extended.json')
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
        kwargs['size'] = (2*radius,2*radius,2*radius)
        PrefabStimulus.__init__(self, pttype="sphere", **kwargs)
        #Default size is 100,100,100

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
    def __init__(self, **kwargs):
        PrefabStimulus.__init__(self, pttype="cube", **kwargs)
        #default size is 102,102,102

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

        self._setGuiCaption('POCore/DebugText', OgreRenderer.debugText)

    def _setGuiCaption(self, elementName, text):
        element = ogre.OverlayManager.getSingleton().getOverlayElement(elementName, False)
        ##d=ogre.UTFString("hell0")
        ##element.setCaption(d)

        #element.caption="hello"

        #element.setCaption("help")
        element.setCaption(text) # ogre.UTFString(text))

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