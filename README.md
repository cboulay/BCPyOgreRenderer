BCPyPandaRenderer
=================

This is a drop-in replacement renderer for [BCPy2000](http://bci2000.org/downloads/BCPy2000/Renderers.html)
using the [OGRE3D](http://www.ogre3d.org/) engine with its [Python-Ogre](http://www.python-ogre.org/) bindings.

This is still very early but the test works. Run `test.bat` to try it out.

## Installation

My [BCPyElectrophys](https://github.com/cboulay/BCPyElectrophys) implementation of BCPy2000 requires Python 2.6.
Therefore, this uses [pre-built python-ogre](http://sourceforge.net/projects/python-ogre/files/Latest/1.6.4%20SnapShot/Python-Ogre-Core-1.6.4-r1017-py263.7z/download) compatible with Python 2.6.
[Install instructions](http://www.cse.unr.edu/~sushil/class/381/ware/pythonOgreWin7Install.pdf).

## Virtual Hand

One reason for using a 3D engine is that I would like to use BCPy2000 to
control the animation of a virtual hand.

I am using [libhand](www.libhand.org). It comes with an OGRE model but that is not compatible with PythonOgre 1.6.4.
Therefore I used the Blender model, then [exported](https://code.google.com/p/blender2ogre/)
to a generic OGRE .xml, then converted it to the correct version using the tools found in the PythonOgre 1.6.4 snapshot release.

## Renderer Life-Cycle

Here I will keep some notes to help me keep track of how things get initialized.

### BCI2000 stage
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

### Import stage. From (3) in the BCI2000 stage.
1. GenericApplication sets a global class VisualStimuli, imported from ... ?

### Instancing stage. From (4) in the BCI2000 stage?
1. TestApplication is imported
2. TestApplication does not define `__init__`, so `GenericApplication.__init__()` is called.
    1. `Core.BciCore.__init__()` #Call's super's init
        1. `Object.__init__()` #Its super's init
        2. `self._threads = {}` #Empty list of threads
    2. `self.screen = None` #Placeholder
    3. self._threads['visual display'] = BciThread(func=self._visual_display, loop=True)` #Messging capable thread is created but not run yet
    4. `self._optimize_display_thread_affinity = False`, `self._optimize_display_thread_priority = False`, `self._optimize_process_priority = False`, `self._display_sleep_msec = -1`

### _start stage. From (5) in the BCI2000 stage.
1. Threads [visual display, console, phase machine] are .start()ed

### Construct phase. From (6) in the BCI2000 stage.
1. GenericApplication._Construct(bci)
    1. `if self._optimize_display_thread_affinity: PrecisionTiming.SetThreadAffinity([0])`
    2. `paramdefs,statedefs = super(BciGenericApplication, self)._Construct()`    # Core's Construct. params and states.
    3. `self._merge_defs(paramdefs, statedefs, self.Construct())` # Our application's Construct. params and states.
    4. If we still don't have a self.screen, instantiate PandaRenderer (or VisionEggRenderer if no renderer is specified)
        1. `PandaRenderer.__init__()` sets some constants. Not much else.
    5. Do something with the VisualStimuli global class

### Preflight and Initialize phase. From (8) in the BCI2000 stage.
1. Calls BciGenericApplication._Preflight
    1. super's _Preflight doesn't do anything relevant to us.
    2. subclass (our app)'s Preflight
        1. self.screen.setup(frameless_window=0)
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
        10. Do a single loop, remove 'init', then do all the loops (as long as the thread doesn't receive a stop message)
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