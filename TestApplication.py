import numpy
import OgreRenderer
import ogre.io.OIS as OIS
from AppTools.StateMonitors import addstatemonitor, addphasemonitor

#################################################################
#################################################################

class BciApplication(BciGenericApplication):

    #############################################################

    def Description(self):
        return "I bet you won't bother to change this to reflect what the application is actually doing"

    #############################################################

    def Construct(self):
        # supply any BCI2000 definition strings for parameters and
        # states needed by this module
        params = [

        ]
        states = [
            "SomeState 1 0 0 0",
        ]

        return params,states

    #############################################################

    def Preflight(self, sigprops):
        # Here is where you would set VisionEgg.config parameters,
        # either using self.screen.setup(), or directly.
        self.screen.setup(frameless_window=0)  # if using VisionEggRenderer, this sets, VISIONEGG_FRAMELESS_WINDOW

    #############################################################

    def Initialize(self, indim, outdim):
        self.color = numpy.array([1.0, 0.0, 0.0])
        # Set up stimuli. Visual stimuli use calls to
        # self.stimulus(). Attach whatever you like as attributes
        # of self, for easy access later on. Don't overwrite existing
        # attributes, however:  using names that start with a capital
        # letter is a good insurance against this.

        #w,h = self.screen.size
        #self.screen.SetDefaultFont('comic sans ms', 30)

        Text = self.VisualStimuli.Text   # the convention is that the self.VisualStimuli "virtual module"
                                         # contains at least Text, Disc, Block and ImageStimulus classes for all renderers
        self.stimulus('SomeText', Text, text='BCPy2000: Python bindings for your brain',
                                        position=(300, 100),
                                        anchor='right'         )
        addstatemonitor(self, 'Running', showtime=True)

        EntityStimulus = OgreRenderer.EntityStimulus
        self.stimulus('hand', EntityStimulus, mesh_name='hand.mesh')
        self.stimuli['hand'].node.setScale(50,50,50)

        #=======================================================================
        # Disc = self.VisualStimuli.Disc
        # self.stimulus('cursor1',  z=3,   stim=Disc(position=(0,0), radius=10, color=(1,1,1), on=True))
        #=======================================================================

        #=======================================================================
        # Block = self.VisualStimuli.Block
        # self.stimulus('block',z=2, stim= Block(position = (0,0), size = (400,400), color=(1, 0.1, 0.1, 0.5), on=True))
        #=======================================================================
        #b = box(size=siz, position=(scrw/2.0,scrh/2.0 - siz[1]/6.0), sticky=True)
        #triangle = PolygonTexture(frame=b, vertices=((0,1),(1,1),(0.5,0)), color=(0,0,0,0.5))

    #############################################################

    def StartRun(self):
        pass

    #############################################################

    def Phases(self):
        # define phase machine using calls to self.phase and self.design
        self.phase(name='flip', next='flop', duration=2000)
        self.phase(name='flop', next='flip', duration=2000)
        self.design(start='flip')

    #############################################################

    def Transition(self, phase):
        pass
        # present stimuli and update state variables to record what is going on
        # if phase == 'flip':
            # self.stimuli['SomeText'].anchor = 'top'
            # self.states['SomeState'] = 1
        # if phase == 'flop':
            # self.stimuli['SomeText'].anchor = 'bottom'
            # self.states['SomeState'] = 0

    #############################################################

    def Process(self, sig):
        pass# process the new signal packet

    #############################################################

    def Frame(self, phase):
        # update stimulus parameters if they need to be animated on a frame-by-frame basis
        intensity = 0.5 + 0.5 * numpy.sin(2.0 * numpy.pi * 0.5 * self.since('run')['msec']/1000.0)
        self.screen.bgcolor = intensity * self.color
        #self.stimuli['hand'].node.yaw(0.02)

    #############################################################

    def Event(self, phase, event):
        # respond to OIS events
        if event.isKeyDown(OIS.KC_ESCAPE):
            print "Escape Pressed"

    #############################################################

    def StopRun(self):
        pass

#################################################################
#################################################################
