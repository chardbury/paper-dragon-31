%~d0

cd %~p0..

set PYTHON=%APPDATA%\..\Local\Programs\Python\Python39\python

if not exist venv (%PYTHON% -m venv venv)

venv\Scripts\python -m pip install -U pip

venv\Scripts\pip install -e .[development]

cmd /k venv\Scripts\activate.bat