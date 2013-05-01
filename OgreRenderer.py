#Based on http://wiki.python-ogre.org/index.php/CodeSnippets_Minimal_Application
#TODO: Text alternate coordinate frames
#TODO: PolygonTexture->ImageStimulus
#TODO: Keyboard events passed to application
#TODO: Fonts
#TODO: Window placement. Removing the border causes unexpected placement
#TODO: Framerate

__all__ = ['Text', 'Block', 'Disc', 'ImageStimulus', 'Movie']

import sys
import os
import os.path
import time
import OgreApplication
import ogre.renderer.OGRE as ogre
import BCPy2000.AppTools.Coords as Coords
try:    from BCI2000PythonApplication    import BciGenericRenderer, BciStimulus   # development copy
except: from BCPy2000.GenericApplication import BciGenericRenderer, BciStimulus   # installed copy
import threading
import Queue

class OgreThread(threading.Thread):
    """The thread in which ogre will render itself.
    This needs to occur in stages (messages):
    1-
    """
    def __init__(self, queue, renderer, app):
        threading.Thread.__init__(self)
        self.queue = queue
        self.renderer = renderer
        self.app = app

    def run(self):
        #Pass variables from OgreRenderer to OgreApplication
        self.app._coords = self.renderer._coords
        self.app._plugins_path = self.renderer._plugins_path
        self.app._resource_path = self.renderer._resource_path
        self.app._screen_scale = self.renderer._screen_scale
        self.app._screen_params = self.renderer._screen_params
        #Initialize the screen
        self.app.createRoot()
        self.app.defineResources()
        self.app.setupRenderSystem()
        self.app.createRenderWindow()
        self.app.initializeResourceGroups()
        self.app.setupScene()
        self.app.createFrameListener()
        #Tell the Renderer thread we are ready
        self.queue.put({'Ready': True})
        #self.app.startRenderLoop()
        msgToStop = False
        while not msgToStop:
            ogre.WindowEventUtilities().messagePump()
            self.app.root.renderOneFrame()
            try:
                msg = self.queue.get(True,0.0001)
                msgToStop = "Stop" in msg.keys() and msg["Stop"]
            except:
                msgToStop = False
        self.app.cleanUp()


class OgreRenderer(BciGenericRenderer):
    debugText=""
    def __init__(self):
        #Set some defaults that aren't defined by setup (i.e. non-parameterizable constants)
        self.framerate = 60.#Returned if we don't really check the framerate
        self.screen = None
        self._bci = None

    def __del__(self):
        "Clear variables, this should not actually be needed."
        del self.thread
        del self.app

    def setup(self, width = 800, height = 600, left = 0, top = 0,
            bgcolor = (0.5, 0.5, 0.5), frameless_window = None, title="BCPyOgre",
            plugins_path = '.\\BCPyOgreRenderer\\plugins.cfg.nt', resource_path = '.\\BCPyOgreRenderer\\resources.cfg',
            coordinate_mapping = 'pixels from center', id=None, scale=None, **kwds):
        """BCI2000 parameters relevant to the display are passed in here,
        during the Application Preflight, either directly or through AppTools.Displays.fullscreen, on the main thread.
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
        self.app = OgreApplication.Application()
        self.ogreQ=Queue.Queue()
        self.thread = OgreThread(self.ogreQ, self, self.app)
        self.thread.setDaemon(True) #Not sure if necessary
        self.thread.start() #Kicks off the run().
        msg = self.ogreQ.get(True, None)#Block progression, with no timeout, until the OgreThread posts it is ready to render
        self.coordinate_mapping = self._coordinate_mapping
        self.color = self._bgcolor

    def GetFrameRate(self):
        if 'FramesPerSecond' in self._bci.estimated:
            return self._bci.estimated['FramesPerSecond']['running']#self.renderWindow.getLastFPS() is too slow to do every frame.
        else: return self.framerate

    def RaiseWindow(self):
        try:
            pass
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
        pass

    def FinishFrame(self):
        pass

    def Cleanup(self):
        self.ogreQ.put({'Stop': True})
        #self.ogreQ.join() #Wait until the OgreApplication is cleaned up before continuing

    def SetDefaultFont(self, name = None, size = None):
        return SetDefaultFont(name=name, size=size)

    def GetDefaultFont(self):
        return GetDefaultFont()

    @property
    def size(self):
        return (self.width,self.height)
    def get_size(self): return self.size
    @property
    def width(self): return self.app.viewPort.getActualWidth()
    @property
    def height(self): return self.app.viewPort.getActualHeight()

    @property
    def bgcolor(self):
        """Color of viewPort.BackgroundColour"""
        return self._bgcolor
    @bgcolor.setter
    def bgcolor(self, value):
        self._bgcolor = value
        self.app.viewPort.setBackgroundColour(self._bgcolor)
    color=bgcolor

    @property
    def coordinate_mapping(self):
        return self._coordinate_mapping
    @coordinate_mapping.setter
    def coordinate_mapping(self, value):
        zpos = self.app.camera.getPosition()[2]
        cm = value.lower().replace('bottom', 'lower').replace('top', 'upper').replace(' ', '')
        scrw,scrh = self.size
        longd = max((scrw,scrh))
        if cm == 'pixelsfromlowerleft': #VisionEgg default
            self.app.camera.setPosition( ogre.Vector3(scrw/2, scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, scrh/2 + 80, -longd/10.0) )
            self.app.light.setPosition ( ogre.Vector3(scrw, scrh, longd) )
        elif cm == 'pixelsfromupperleft': #PygameRenderer default
            self.app.camera.setPosition( ogre.Vector3(scrw/2, -scrh/2, zpos) )
            #self.light.setPosition ( ogre.Vector3(-scrw/2 - 20, -scrh/2 + 80, -longd/10.0) )
            self.app.light.setPosition ( ogre.Vector3(scrw, -scrh, longd) )
        elif cm == 'pixelsfromcenter': #OgreRenderer default
            self.app.camera.setPosition( ogre.Vector3(0, 0, zpos) )
            #self.light.setPosition ( ogre.Vector3(20, 80, -longd/10.0) )
            self.app.light.setPosition ( ogre.Vector3(scrw/2, scrh/2, longd/5.0) )
        else:
            raise ValueError('coordinate_mapping "%s" is unsupported' % value)
        self._coordinate_mapping = value

BciGenericRenderer.subclass = OgreRenderer

class OgreStimulus(Coords.Box):
    """Superclass for EntityStimulus and Text.
    Contains a FEW common functions. DRY"""
    def __init__(self, size=(1,1,1), color=None, position=(0,0,0), anchor='center', on=True, sticky=False, **kwargs):
        Coords.Box.__init__(self)
        self.ogr = ogre.Root.getSingleton()
        #Set desired anchor, position, and size then reset
        super(OgreStimulus, self.__class__).anchor.fset(self, anchor)
        super(OgreStimulus, self.__class__).position.fset(self, position)
        self.sticky = sticky#This doesn't affect anything so we can use the direct access
        self.size = size#This will cause the reset
        if color: self.color = color
        self.on = on

    @property
    def size(self):
        #Subclass should overshadow this to get the real size from the object and set the internal size
        return Coords.Box.size.fget(self)
    @size.setter
    def size(self, value):
        value = tuple(value)
        while len(value)<3: value = value + (None,) #Fill out til it's 3D
        value = tuple([x if x else 1.0 for x in value])#Replace None's with 1's
        super(OgreStimulus, self.__class__).size.fset(self, value)
        self.reset()
    @property
    def width(self):
        return self.size.x #Returns updated representation
    @width.setter
    def width(self, value):
        super(OgreStimulus, self.__class__).width.fset(self, value)
        self.reset()
    @property
    def height(self):
        return self.size.y
    @height.setter
    def height(self, value):
        super(OgreStimulus, self.__class__).height.fset(self, value)
        self.reset()
    @property
    def depth(self):
        return self.size.z
    @depth.setter
    def depth(self, value):
        super(OgreStimulus, self.__class__).depth.fset(self, value)
        self.reset()
    def scale(self, value):
        if not isinstance(value, (tuple,list)): value = tuple([value])
        while len(value)<3: value = value + (value[-1], )
        self.size = self.size * value

    @property
    def position(self):
        #Subclass should overshadow this to get the real position and set the internal variable
        return super(OgreStimulus, self).position
    @position.setter
    def position(self, value):
        #Account for None in value
        currAnchPos = self.position
        newAnchPos = [new if new else old for new,old in zip(value,currAnchPos)]
        super(OgreStimulus, self.__class__).position.fset(self, newAnchPos)
        self.reset()
    @property
    def x(self):
        return self.position.x #This updates __position with the true position.
    @x.setter
    def x(self, value):
        super(OgreStimulus, self.__class__).x.fset(self, value)
        self.reset()
    @property
    def y(self):
        return self.position.y #This updates __position with the true position.
    @y.setter
    def y(self, value):
        super(OgreStimulus, self.__class__).y.fset(self, value)
        self.reset()
    @property
    def z(self):
        return self.position.z #This updates __position with the true position.
    @z.setter
    def z(self, value):
        super(OgreStimulus, self.__class__).z.fset(self, value)
        self.reset()

    #Others: lims,rect,left,right,top,bottom,near,far
    @property
    def lims(self):
        self.position
        self.size
        return super(OgreStimulus, self).lims
    @lims.setter
    def lims(self, value):
        super(OgreStimulus, self.__class__).lims.fset(self, value)
        self.reset()
    @property
    def rect(self):
        self.position
        self.size
        return super(OgreStimulus, self).rect
    @rect.setter
    def rect(self, value):
        super(OgreStimulus, self.__class__).rect.fset(self, value)
        self.reset()
    @property
    def left(self):
        self.position
        self.size
        return super(OgreStimulus, self).left
    @left.setter
    def left(self, value):
        super(OgreStimulus, self.__class__).left.fset(self, value)
        self.reset()
    @property
    def right(self):
        self.position
        self.size
        return super(OgreStimulus, self).right
    @right.setter
    def right(self, value):
        super(OgreStimulus, self.__class__).right.fset(self, value)
        self.reset()
    @property
    def top(self):
        self.position
        self.size
        return super(OgreStimulus, self).top
    @top.setter
    def top(self, value):
        super(OgreStimulus, self.__class__).top.fset(self, value)
        self.reset()
    @property
    def bottom(self):
        self.position
        self.size
        return super(OgreStimulus, self).bottom
    @bottom.setter
    def bottom(self, value):
        super(OgreStimulus, self.__class__).bottom.fset(self, value)
        self.reset()
    @property
    def near(self):
        self.position
        self.size
        return super(OgreStimulus, self).near
    @near.setter
    def near(self, value):
        super(OgreStimulus, self.__class__).near.fset(self, value)
        self.reset()
    @property
    def far(self):
        self.position
        self.size
        return super(OgreStimulus, self).far
    @far.setter
    def far(self, value):
        super(OgreStimulus, self.__class__).far.fset(self, value)
        self.reset()

    @property
    def anchor(self):
        return super(OgreStimulus, self).anchor
    @anchor.setter
    def anchor(self, value):
        super(OgreStimulus, self.__class__).anchor.fset(self, value)
        self.reset()

class EntityStimulus(OgreStimulus):
    """Creates a 3D Ogre object using provided mesh or entity.
    """
    def __init__(self, mesh_name='hand.mesh', entity=None, parent=None, **kwargs):
        #Coords.Box.__init__(self)
        #self.ogr = ogre.Root.getSingleton()
        #self.sceneManager = self.ogr.getSceneManager("Default SceneManager")
        ogr = ogre.Root.getSingleton()
        self.sceneManager = ogr.getSceneManager("Default SceneManager")

        #Unique to this class
        self.entity = entity if entity else self.sceneManager.createEntity(mesh_name + 'Entity', mesh_name)
        parent = parent if parent else self.sceneManager.getRootSceneNode()
        self.node = parent.createChildSceneNode(self.entity.getName() + 'Node', (0,0,0))
        self.node.attachObject(self.entity)
        orig_size = self.entity.getBoundingBox().getSize()
        self.__original_size = Coords.Size((orig_size[0],orig_size[1],orig_size[2]))
        #Common settings
        OgreStimulus.__init__(self, **kwargs)

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
        #Position
        anch = [-1*a if neg else a for a,neg in zip(anch,negDim)]#Reposition the anchor if we have any negative sizes
        desiredNodePos = desiredAnchPos - anch*desiredSize/2#Unadjust the anchor position to get node position
        self.node.setScale(desiredScale[0],desiredScale[1],desiredScale[2])
        self.node.setPosition(desiredNodePos[0],desiredNodePos[1],desiredNodePos[2])

    @property
    def size(self):
        trueSize = self.entity.getWorldBoundingBox().getSize()
        trueSize = (trueSize[0], trueSize[1], trueSize[2])#Convert from Ogre to tuple
        if trueSize[0]==0 and trueSize[1]==0 and trueSize[2]==0: #Not yet in the world.
            trueSize = self.__original_size
        Coords.Box.size.fset(self, trueSize)
        return super(EntityStimulus, self).size
    @size.setter
    def size(self,value):
       super(EntityStimulus, self.__class__).size.fset(self, value)

    @property
    def position(self):
        nodePos = self.node.getPosition() #Get the true position
        nodePos = Coords.Point([nodePos[0], nodePos[1], nodePos[2]]) #Convert to screen coordinates
        anchorPos = nodePos+self.anchor*self.size/2 #Adjust for the anchor
        Coords.Box.position.fset(self, anchorPos)
        return super(EntityStimulus, self).position
    @position.setter
    def position(self,value):
        super(EntityStimulus, self.__class__).position.fset(self, value)

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
		self.__pose_ix = pose_ix
        for key in pose: #key = "finger4joint2"
            bone = skel.getBone(key)
            bone.setOrientation(pose[key])
	def getPose(self):
		return self.__pose_ix

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

    @property
    def testprop(self):
        print "testprop getter"
        return 0
    @testprop.setter
    def testprop(self):
        print "testprop setter"

    def get_getset(self):
        print "getset getter"
        return 0
    def set_getset(self, value):
        print "getset setter"
    getset = property(get_getset, set_getset)

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

class Text(OgreStimulus):
    """Docstring"""
    def __init__(self, text='Hello world', font_name="BlueHighway",\
                  font_size=16, angle=0.0, smooth=True, **kwargs):
        #angle and smooth get eaten because I have no idea what they do

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
        #Store the variables
        self.overlay = overlay
        self.panel = panel
        self.textArea = textArea
        #Some settings
        self.text = text
        self.font_name = "BlueHighway"
        self.font_size = font_size
        #self.font_name = font_name #TODO: Fonts!
        self.__original_size = Coords.Size((len(text)*font_size/(16.0/6),font_size,1.0))
        #Common init steps: anchor, position, sticky, size, color, on
        OgreStimulus.__init__(self, **kwargs)


    def reset(self):
        desiredSize = super(Text, self).size
        anch = self.anchor
        desiredAnchPos = super(Text, self).position
        #Account for negative sizes
        negDim = [x<0 for x in desiredSize]
        desiredSize = [-siz if neg else siz for siz,neg in zip(desiredSize,negDim)]
        desiredSize = Coords.Size([siz if siz>0 else 1.0 for siz in desiredSize])#Make sure we never try to set size to 0
        #Scale
        origSize = self.__original_size
        desiredScale = desiredSize/origSize
        #Position
        anch = [-1*a if neg else a for a,neg in zip(anch,negDim)]#Reposition the anchor if we have any negative sizes
        panL = desiredAnchPos[0] - (anch[0]+1)*(desiredSize[0]/2)
        panT = desiredAnchPos[1] - (1-anch[1])*(desiredSize[1]/2)
        self.panel.setDimensions(desiredScale[0],desiredScale[1])
        self.panel.setPosition(panL,panT)

    @property
    def size(self):
        trueSize = (self.panel.getHeight(), self.panel.getWidth(), 0)
        if trueSize[0]==0 and trueSize[1]==0 and trueSize[2]==0: #Not yet in the world.
            trueSize = self.__original_size
        Coords.Box.size.fset(self, trueSize)
        return super(Text, self).size
    @size.setter
    def size(self,value):
        super(Text, self.__class__).size.fset(self, value)

    @property
    def position(self):
        t,l,w,h = self.panel.getTop(), self.panel.getLeft(), self.panel.getHeight(), self.panel.getWidth()
        a = self.anchor
        aX = l + (a[0]+1)*w/2
        aY = t + (1-a[1])*h/2
        Coords.Box.position.fset(self, (aX,aY,0))
        return super(Text, self).position
    @position.setter
    def position(self,value):
        value = tuple(value)
        while len(value)<3: value = value + (None,)
        super(Text, self.__class__).position.fset(self, value)

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