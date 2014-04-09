#! ../prod/prog/BCI2000Shell
@cls & ..\prod\prog\BCI2000Shell %0 %* #! && exit /b 0 || exit /b 1\n
Change directory $BCI2000LAUNCHDIR
execute script ..\batch\FindPortablePython.bat  # this is necessary so that BCI2000 can find Python
Show window; Set title ${Extract file base $0}
Reset system
Startup system localhost
Start executable SignalGenerator --local
Start executable SpectralSignalProcessing --local
Start executable PythonApplication --local --PythonAppClassFile=..\..\BCPyOgreRenderer\TemplateApplication.py --PythonAppWD=..\..\BCPyOgreRenderer
Wait for Connected
Load parameterfile "../../BCPyOgreRenderer/test_dropin.prm"