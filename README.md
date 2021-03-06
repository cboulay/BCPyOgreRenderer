BCPyOgreRenderer
=================

BCPyOgreRenderer is a drop-in replacement renderer for [BCPy2000](http://bci2000.org/downloads/BCPy2000/Renderers.html)
using the [OGRE3D](http://www.ogre3d.org/) engine with its [Python-Ogre](http://www.python-ogre.org/) bindings.
This is only meant as a temporary way to get easy access to a 3D engine in BCI2000. Other methods are being developed and will surpass this.

## Important Note

Since I am now using an older Python-Ogre, the models included with this repo are too new and no longer work. They must be re-exported from Blender for the correct version.

## Installation

At first I intended this to be used with [BCPyElectrophys](https://github.com/cboulay/BCPyElectrophys).
However, since my approach to using a 3D engine will change soon, I am dissociating the two and am no longer concerned with keeping their Python versions compatible.

If you have not already done so, please install BCI2000 and BCPy2000. See InstallBCPy2000.txt in this repository.

1. Clone this repository.
	- If you would like to use a GUI-based Git client, I suggest [SourceTree](http://www.sourcetreeapp.com/).
2. Copy this repository's root folder to be a sister directory to your BCI2000 production folder. e.g.,
	- C:\BCI2000\dev
	- C:\BCI2000\prod
	- C:\BCI2000\FullMonty254-2011-710
	- C:\BCI2000\BCPyOgreRenderer
3. Edit the plugins.cfg file to point to the directory where Python-Ogre's plugins folder is.
	- Note that the directory is relative to the PythonAppWD (working directory).
4. Edit the resources.cfg file to point to the media you will use (3D objects, materials, etc.)
	- Note that the directory is relative to the PythonAppWD.
5. Edit test_dropin.bat
	- The top two lines point to the location of the BCI2000 prog directory, relative to the location of test_drop.bat
	- Line 9, PythonAppClassFile points to the location, relative to the BCI2000 prog directory, of the BCPy2000 application file.
	- Line 9, PythonAppWD points to the location, relative to the BCI2000 prog directory, where all your support files are.
		- This is also the location that plugins.cfg and resources.cfg start in to search for their respective items.
		
Run `test_dropin.bat` to try it out.

## Notes

To maintain compatibility with other BCPy2000 applications I've used the myApp.stimulus() convention.
This wraps the stimulus objects in a BciStimulus object. e.g.:

`hand = myApp.stimuli['hand']`

where `hand` is a BciStimulus object. The BciStimulus object conveniently exposes the actual object's properties. e.g.:

`hand.x = 10` is equivalent to `hand.obj.x = 10`

This is not true for `z`. i.e., `hand.z = 10` is not equivalent to `hand.obj.z = 10`. For a BciStimulus object,
.z has a different meaning. Therefore I recommend to avoid confusion by always operating on the stimulus.obj position.

### Virtual Hand

One reason for using a 3D engine is that I would like to use BCPy2000 to control the animation of a virtual hand.
I am using [libhand](http://www.libhand.org). It comes with an OGRE model that is compatible with Ogre 1.7.1 (linked above).
If for some reason you use a different Ogre version, you may use the Blender model, then [export it](https://code.google.com/p/blender2ogre/)
to a generic OGRE .xml, then converted it to the correct version using the [tools](http://sourceforge.net/projects/ogre/files/ogre-tools/) for your version of Ogre.

### Renderer Life-Cycle

Here I will keep some notes to help me keep track of how things get initialized.

#### BCI2000 stage
BCI2000 treats the PythonFilter as any other filter. Most of the C++ code is unreadable to me, but I found a few things in PythonFilter.cpp that might help me understand what's going on.

1. `Py_Initialize()`
2. `PyEval_InitThreads()`
3. EvalPythonString to import core and generic modules
4. Calls __main__ of the developer file
5. `CallMethod("_start");`
6. `CallHook("_Construct");`
7. Get the Python parameters and states into BCI2000
8. Upon "Set Config"
    1. _Preflight
    2. _Initialize
9. Upon "Run"
    1. _StartRun
    2. _Process
    3. _StopRun

#### Import stage. From (3) in the BCI2000 stage.
1. GenericApplication sets a global class VisualStimuli, imported from ... ?

#### Instancing stage. From (4) in the BCI2000 stage?
1. TestApplication is imported
2. TestApplication does not define `__init__`, so `GenericApplication.__init__()` is called.
    1. `Core.BciCore.__init__()` #Call's super's init
        1. `Object.__init__()` #Its super's init
        2. `self._threads = {}` #Empty list of threads
    2. `self.screen = None` #Placeholder
    3. self._threads['visual display'] = BciThread(func=self._visual_display, loop=True)` #Messaging capable thread is created but not run yet
    4. `self._optimize_display_thread_affinity = False`, `self._optimize_display_thread_priority = False`, `self._optimize_process_priority = False`, `self._display_sleep_msec = -1`

#### _start stage. From (5) in the BCI2000 stage.
1. Threads [visual display, console, phase machine] are .start()ed

#### Construct phase. From (6) in the BCI2000 stage.
1. GenericApplication._Construct(bci)
    1. `if self._optimize_display_thread_affinity: PrecisionTiming.SetThreadAffinity([0])`
    2. `paramdefs,statedefs = super(BciGenericApplication, self)._Construct()`    # Core's Construct. params and states.
    3. `self._merge_defs(paramdefs, statedefs, self.Construct())` # Our application's Construct. params and states.
    4. If we still don't have a self.screen, instantiate OgreRenderer (or VisionEggRenderer if no renderer is specified)
        1. `OgreRenderer.__init__()` sets some constants. Not much else.
    5. Do something with the VisualStimuli global class

#### Preflight and Initialize phase. From (8) in the BCI2000 stage.
1. Calls BciGenericApplication._Preflight
    1. super's _Preflight doesn't do anything relevant to us.
    2. subclass (our app)'s Preflight
        - `self.screen.setup(frameless_window=0)` is our renderer setup
        - or `fullscreen(scale=float(self.params['WindowSize']), id=int(self.params['ScreenId']), frameless_window=(siz==1))`
        - or don't use either and we will use ogre.cfg instead.
2. Calls BciGenericApplication._Initialize
    1. super's _Initialize not relevant here.
    2. Get the 'visual display' thread, make sure it is ready, then post 'init'
        1. `self.screen.Initialize(self)`
        2. `self._initfocus()`
        3. Prepares some variables (self.stimuli, self._stimlist, self._stimz, self._stimq)
        4. `self.Initialize(self.in_signal_dim, self.out_signal_dim)` #Our application's Initialize hook
            1. Setup the visual stimuli here
        5. `self.focus('stimuli')`
        6. `fr = self.screen.GetFrameRate()`
        7. Use self._optimize_display_thread_affinity and self.optimize_display_thead_priority
        8. `self.focus('operator')`
        9. `mythread.read('init', remove=False)`
        10. Do a single frame, remove 'init', then do all the loops (as long as the thread doesn't receive a stop message)
            1. `events = self.screen.GetEvents()` #Logged (ftdb)
            2. `self._lock.acquire('Frame') #Logged
            3. if running, do Event+Frame
                1. for each event, `self.Event(self.current_presentation_phase, event)`
                2. `self.Frame(self.current_presentation_phase)`
                3. `self._run_callbacks('Frame')`
            4. self._update_stimlist() #Logged
            5. self.screen.StartFrame(self._stimlist) #internally logged
            6. self._lock.release('Frame' #Logged
            7. sleep #Logged
            8. self.screen.FinishFrame() #Logged
            9. frame count, end iteration #Logged
        11. `self._lock.release('Frame')`
        12. `self.screen.Cleanup()`

### Stimulus Life-Cycle

#### Initialize
1. `myApp.stimulus(name, stimClass, z=0, **kwargs)`
    1. Makes sure myApp has .stimuli, ._stimlist, ._stimz, ._stimq
    2. `s = BciStimulus(myApp, name, z)`
        - This is a wrapper object for stimuli
        - It has .z and .obj attributes, where .obj is the actual stimulus object
        - It exposes .leave() and .enter() for the stimz queue
        - It might also expose the .obj.* attributes as s.* attributes (or parameters.* attributes to s.* attributes for VisionEgg stimuli)
    3.  Passes the stimClass through Core.BciFunc to get maker, passes along the kwargs, `s._maker = maker`
        - maker is just a wrapper for the callable (I guess the callable is the class instantiation)
        - maker remembers its original pargs and kwargs, allows new kwargs to be added on subsequent calls, and allows pargs to be suppressed with new pargs on subsequent calls
    4. `s.enter()`
        1. Appends the stimulus to myApp._stimq and sets it in myApp.stimuli dict
    5. return s

#### Rendering
In the case of VisionEggRenderer

1. myApp._update_stimlist()
    1. Runs itself on each of _stimq
    2. Each _stimq z-val is inserted into self._stimz at the appropriate index for its z-val, and the stim object itself is inserted into self._stimlist at the appropriate index
2. myApp.screen.StartFrame(myApp._stimlist)
    1. Clear the screen
    2. `myApp.screen._viewport.parameters.stimuli = myApp._stimlist` #myApp.screen._viewport = VisionEgg.Core.Viewport(screen=self._screen)
    3. `myApp.screen._viewport.draw()`

I guess that means that VisionEggRenderer requires the stimuli to be in order according to the z-value. In our case, that isn't necessary.
How can we still use the myApp.stimulus function but save cycles on _update_stimlist because we don't need it?