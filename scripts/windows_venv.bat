%~d0

cd %~p0..

if not exist venv (%LOCALAPPDATA%\Programs\Python\Python39\python -m venv venv)

venv\Scripts\python -m pip install -U pip wheel

venv\Scripts\pip install -e .[development]

cmd /k venv\Scripts\activate.bat