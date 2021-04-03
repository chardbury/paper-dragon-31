%~d0

cd %~p0..

venv\Scripts\python -c "import applib.constants; print(applib.constants.APPLICATION_NAME);" > temp_application_name

set /p APPLICATION_NAME= < temp_application_name

del temp_application_name

venv\Scripts\pyi-makespec ^
    --onefile --windowed --noupx ^
    --add-data data;data ^
    --icon data\icons\icon.ico ^
    --name "%APPLICATION_NAME%" ^
    scripts\pyinstaller_start.py

venv\Scripts\pyinstaller --noconfirm "%APPLICATION_NAME%.spec"

del "%APPLICATION_NAME%.spec"
