import numpy as np
from random import randint, uniform, random, shuffle
from math import ceil, sqrt
import time
import OgreRenderer as OgreRenderer
from OgreRenderer import HandStimulus, Disc, Block, Text
import SigTools
from AppTools.Boxes import box
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
#from AppTools.Shapes import Disc

class BciApplication(BciGenericApplication):

    def Description(self):
        return "Hand animation."

    #############################################################
    def Construct(self):
        #See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
        #See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
        params = [
            "PythonApp:Design   list    GoCueText=      1 Imagery % % % // Text for cues. Defines N targets",
            "PythonApp:Design   float   GoThresh=       1.5 % % %      // Animation or movement starts when signal crosses value",
            "PythonApp:Design   float   ReverseThresh=  0.5 % % %       // Animation/movement reverses when signal goes below value",
            "PythonApp:Design   int     FeedbackType=   0 0 0 2         // Feedback: 0 Libhand, 1 Incong Libhand, 2 Ball (enumeration)",
            ]
        states = [
            #===================================================================
            "Baseline 1 0 0 0", #Sometimes useful for Normalizer.
            "GoCue 1 0 0 0",
            "Task 1 0 0 0",
            "TargetClass 4 0 0 0", #Sometimes useful for Normalizer.
            "RulerOffset 16 0 0 0", #Leftward displacement of the ruler from the right-most position (i.e. from where 0 is at the left edge, displacement will have 0 offscreen to the left by x mm)
            "ShouldAnim 2 0 0 0", #0 for not moving, 1 for moving backwards, 2 for moving forwards
            "IsAnim 2 0 0 0", #0 for not moving, 1 for moving backwards, 2 for moving forwards
            #"AnimPcnt 8 0 0 0", #How far through the movement or animation is the feedback object.
        ]        
        return params,states

    #############################################################
    def Preflight(self, sigprops):
        pass
        #TODO: Check parameters

    #############################################################
    def Initialize(self, indim, outdim):
        #=======================================================================
        # Make a few variables easier to access, especially those accessed every packet.
        #=======================================================================
        self.go_thresh = self.params['GoThresh'].val
        self.rev_thresh = self.params['ReverseThresh'].val
        self.fbpos = (8, -50, -56.5)
        
        #=======================================================================
        # Screen
        #=======================================================================
        self.screen.color = (0,0,0) #let's have a black background
        self.scrw,self.scrh = self.screen.size #Get the screen dimensions.
        self.screen.app.camera.position = (0, 0, 0)
        self.screen.app.camera.lookAt ((0, -35, -40))
        self.screen.app.camera.nearClipDistance = 1
        import ogre.renderer.OGRE as ogre
        self.screen.app.camera.setFOVy(ogre.Degree(21.2))
        
        #=======================================================================
        # Register the cue text stimuli.
        #=======================================================================
        self.stimulus('cue', z=5, stim=VisualStimuli.Text(text='?', position=(400,400,0), anchor='center', color=(1,1,1), font_size=50, on=True))
        self.stimuli['cue'].on = False
        
        #=======================================================================
        # Create the ruler
        #=======================================================================
        # #import ogre.renderer.OGRE as ogre
        # ovm = ogre.OverlayManager.getSingleton()
        # screen = ovm.getOverlayElement("screen")
        # ve = screen.getChild("visionegg")
        # #self.ruler = ovm.getByName("MyOverlays/Ruler")
        # #self.ruler.show()
        # self.ruler = ovm.createOverlayElement("Panel","Ruler")
        # self.ruler.setMaterialName("MyMaterials/Ruler")
        # self.ruler.setMetricsMode(ogre.GMM_PIXELS)
        # #the ruler png is 8032 x 318
        # rulerw = self.scrw*2
        # rulerh = rulerw * 318.0/8032.0
        # self.ruler.setWidth(rulerw)
        # self.ruler.setHeight(rulerh)
        # self.ruler.setTop(self.scrh/2.0 - rulerh)
        # ve.addChild(self.ruler)
        # self.ruler.hide()
        self.ruler = OgreRenderer.EntityStimulus(mesh_name = 'Cube.mesh')
        x = 5.0
        self.ruler.node.scale(x, x, x)
        self.ruler.node.setPosition(self.fbpos)
        self.ruler.node.setVisible(False)
        
        #=======================================================================
        # Create the guillotine
        #=======================================================================
        self.guillotine = OgreRenderer.EntityStimulus(mesh_name = 'Box01.mesh') #starts off Vector3(63.7515, 3.38875, 86.0819)
        self.guillotine.node.setPosition(self.fbpos)
        self.guillotine.node.translate((0, 10, 0))
        self.guillotine.node.scale(0.1, 0.1, 0.1)
        self.guillotine.node.pitch(ogre.Degree(90))
        self.guillotine.node.setVisible(False)
        
        #=======================================================================
        # Create the feedback
        #=======================================================================
        if self.params['FeedbackType'].val == 0 or self.params['FeedbackType'].val == 1:
            self.feedback = OgreRenderer.HandStimulus()
            self.feedback.node.yaw(ogre.Degree(-60))
            self.feedback.node.roll(ogre.Degree(-40))
            self.feedback.node.pitch(ogre.Degree(10))
            #self.feedback.on = True
            animState = self.feedback.entity.getAnimationState('my_animation')
            animState.Loop = False
            animState.timePosition = animState.length
            animState.Enabled = True
            #print self.feedback.entity.getWorldBoundingBox().getSize()
            #Vector3(21.9954, 5.94256, 6.04828)
        elif self.params['FeedbackType'].val == 2:
            self.feedback = Disc()
            self.feedback.node.scale(0.05, 0.05, 0.05)
            self.feedbackspd = 12 #ogreunits / second
        self.feedback.node.setPosition(self.fbpos)
        self.feedback.node.setVisible(False)
        if self.params['FeedbackType'].val == 1:
            self.feedback.node.yaw(ogre.Degree(-180))
        
        #=======================================================================
        # State monitors for debugging.
        #=======================================================================
        if int(self.params['ShowSignalTime']):
            # turn on state monitors iff the packet clock is also turned on
            addstatemonitor(self, 'Running', showtime=True)
            addstatemonitor(self, 'CurrentBlock')
            addstatemonitor(self, 'CurrentTrial')
            addstatemonitor(self, 'TargetClass')
            addphasemonitor(self, 'phase', showtime=True)
            addstatemonitor(self, 'RulerOffset')
            addstatemonitor(self, 'ShouldAnim')
            addstatemonitor(self, 'IsAnim')
            addstatemonitor(self, 'AnimPcnt')

            m = addstatemonitor(self, 'fs_reg')
            m.func = lambda x: '% 6.1fHz' % x._regfs.get('SamplesPerSecond', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fs_avg')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('global', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fs_run')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('running', 0)
            m.pargs = (self,)
            m = addstatemonitor(self, 'fr_run')
            m.func = lambda x: '% 6.1fHz' % x.estimated.get('FramesPerSecond',{}).get('running', 0)
            m.pargs = (self,)
        
    #############################################################
    def Halt(self):
        pass

    #############################################################
    def StartRun(self):
        self.forget('task_start') #Initialize this timekeeper at t=0.
        self.forget('range_ok')

    #############################################################
    def StopRun(self):
        pass
        
    #############################################################
    def Phases(self):
        futsuu = self.states['CurrentTrial'] > 0 and self.states['CurrentTrial'] < self.params['TrialsPerBlock'].val-2
        if futsuu:
            # define phase machine using calls to self.phase and self.design
            self.phase(name='intertrial', next='baseline', duration=1000.0)
            self.phase(name='baseline', next='gocue', duration=4000.0)
            self.phase(name='gocue', next='task', duration=1000.0)
            self.phase(name='task', next='stopcue',duration=7000.0)
            self.phase(name='stopcue', next='intertrial', duration=1000.0)
            self.design(start='intertrial', new_trial='intertrial') #It's possible to add a stop phase but so far I have been unsuccessful.
        elif self.states['CurrentTrial'] == self.params['TrialsPerBlock'].val-2:
            #Do guillotine
            self.phase(name='intertrial', next='guilloshow', duration=0.0)
            self.phase(name='guilloshow', next='guillowait', duration=500.0)
            self.phase(name='guillowait', next='guillomove', duration=800.0)
            self.phase(name='guillomove', next='guillotest', duration=200.0)
            self.phase(name='guillotest', next='intertrial', duration=6000.0)
            self.design(start='intertrial', new_trial='intertrial')
        else:
            #Do ruler
            self.phase(name='preRun', next='intertrial', duration=5000.0)
            self.phase(name='intertrial', next='ruler', duration=0.0)
            self.phase(name='ruler', next='intertrial', duration=5000.0)
            self.design(start='preRun', new_trial='intertrial')

    #############################################################
    def Transition(self, phase):
        # Phase information is recorded in a state called PresentationPhase
        # but sometimes it is necessary to have more direct access, 
        # especially for the Normalizer.
        self.states['Baseline'] = int(phase in ['baseline'])
        self.states['GoCue'] = int(phase in ['gocue'])
        self.states['Task'] = int(phase in ['task'])
        
        #Ruler phases
        if phase == 'ruler':
            ruler_offset = int(uniform(28,89))
            #self.ruler.setLeft(-1*ruler_offset)
            self.ruler.node.setPosition(self.fbpos)
            self.ruler.node.translate((-1*ruler_offset, 0, 0))
            self.states['RulerOffset'] = ruler_offset
            self.feedback.node.setVisible(False)
            #self.ruler.show()
            self.ruler.node.setVisible(True)
        else:
            #self.ruler.hide()
            self.ruler.node.setVisible(False)

        #Guillotine phases
        if phase == 'guilloshow': #200 msec
            self.guillotine.node.setVisible(True)
            self.guillotine.move(new_position = (self.fbpos[0]-2, self.fbpos[1]+14, self.fbpos[2]), duration = 0.5)
        elif phase == 'guillowait':
            pass
        elif phase == 'guillomove': #200 msec
            self.guillotine.move(new_position = (self.fbpos[0]-2, self.fbpos[1]+5, self.fbpos[2]), duration = 0.2)
        elif phase == 'guillotest':
            pass
        else:
            self.guillotine.node.setVisible(False)
            self.guillotine.node.setPosition((self.fbpos[0]-2, self.fbpos[1]+25, self.fbpos[2]))

        #trial phases
        if phase == 'intertrial':
            self.states['ShouldAnim'] = 0 #Not moving.
            if self.states['CurrentTrial'] > 1 and self.states['CurrentTrial'] < self.params['TrialsPerBlock'].val-1:
                self.feedback.node.setVisible(True)
        elif phase == 'baseline':
            pass
        elif phase == 'gocue':
            self.stimuli['cue'].text = self.params['GoCueText'][0]          #Change the cue text to the target text.
            self.states['TargetClass'] = 1                                  #Record that the target is now on the screen.
        elif phase == 'task':                                               #Reset variables relevant for task monitoring.
            self.states['ShouldAnim'] = 2                                   #Free to move forward or backward.
        elif phase == 'stopcue':
            self.stimuli['cue'].text = "Relax"
            self.states['ShouldAnim'] = 1                                   #Free to move backward only.
            self.states['TargetClass'] = 0

        self.stimuli['cue'].on = phase in ['gocue', 'stopcue']
        
    #############################################################
    def Process(self, sig):
        #Process is called on every packet/block. This is used for real-time feedback.
        wasAnim = self.states['IsAnim']
        shouldAnim = self.states['ShouldAnim'] #Based on the phase only.        
        if self.in_phase('task'):
            x = sig[0,:].mean(axis=1)
            x = x.A.ravel()[0]
            if x >= self.go_thresh:
                self.states['IsAnim'] = 2 #Set the state to reflect we should be moving forward.
            elif x <= self.rev_thresh: #We are now below the reverse threshold.
                self.states['IsAnim'] = 1 #Change the state to reflect we should be moving backward.
        willAnim = self.states['IsAnim']
        
        ishand = self.params['FeedbackType'].val < 2
        
        ## Control the feedback
        
        ## Hand
        if ishand:
            animState = self.feedback.entity.getAnimationState('my_animation')
            if self.states['ShouldAnim'] == 0:
                animState.TimePosition = animState.Length
                self.states['IsAnim'] = 0
            elif self.states['ShouldAnim'] == 1 and wasAnim != 1: #May only move backward and was not moving backward.
                tp = animState.TimePosition
                tl = animState.Length
                if tp < tl: #If we aren't already at the end.
                    newtp = tl - tp if tp < tl/2.0 else tp #Go past halfway if we are below halfway
                    animState.TimePosition = newtp
                    self.feedback.entity.pause['my_animation'] = False
                    self.states['IsAnim'] = 1
            elif self.states['ShouldAnim'] == 2: #May move forward or backward.
                if wasAnim == 2 and willAnim == 2: #Were and still are moving forward.
                    self.feedback.entity.pause['my_animation'] = animState.TimePosition >= animState.Length/2.0
                elif wasAnim != willAnim: #Need to switch what we are doing
                    self.feedback.entity.pause['my_animation'] = False #Definitely do not need to pause
                    tp = animState.TimePosition
                    tl = animState.Length
                    if willAnim == 2: #Moving forward.
                        animState.TimePosition = tl - tp if tp > tl/2.0 else tp
                    if willAnim == 1: #Moving backward
                        animState.TimePosition = tl - tp if tp < tl/2.0 else tp
                self.states['IsAnim'] = willAnim
        #Ball
        else:
            currpos = self.feedback.node.getPosition()
            if self.states['ShouldAnim'] == 0: #We should not move/animate right now.
                self.states['IsAnim'] = 0
            elif self.states['ShouldAnim'] == 1 and wasAnim != 1: #May only move backward and was not moving backward.
                #TODO: Adjust duration to keep the speed constant.
                dest = self.fbpos
                mvec = [dest[ix] - currpos[ix] for ix in range(0,3)]
                mdist = sqrt(sum([mvec[ix]**2 for ix in range(0,3)]))
                mdur = mdist / self.feedbackspd
                self.feedback.move(new_position = dest, duration = mdur)#Reverse direction
            elif self.states['ShouldAnim'] == 2: #May move forward or backward.
                if wasAnim == 2 and willAnim == 2: #Were and still are moving forward.
                    pass#pause if at max
                elif wasAnim != willAnim: #Need to switch what we are doing
                    if willAnim == 2: #Moving forward.
                        #TODO: Adjust duration to keep the speed constant.
                        dest = (self.fbpos[0], self.fbpos[1]+12, self.fbpos[2])
                    if willAnim == 1: #Moving backward
                        dest = self.fbpos
                    if willAnim == 1 or willAnim == 2: #Do I need this assertion?
                        mvec = [dest[ix] - currpos[ix] for ix in range(0,3)]
                        mdist = sqrt(sum([mvec[ix]**2 for ix in range(0,3)]))
                        mdur = mdist / self.feedbackspd
                        self.feedback.move(new_position = dest, duration = mdur)#Reverse direction
                self.states['IsAnim'] = willAnim
    #############################################################
    def Frame(self, phase):
        # update stimulus parameters if they need to be animated on a frame-by-frame basis
        pass

    #############################################################
    def Event(self, phase, event):
        pass

#################################################################
#################################################################