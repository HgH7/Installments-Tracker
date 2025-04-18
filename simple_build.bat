@echo off
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install customtkinter==5.2.0
python -m pip install tkcalendar==1.6.1
python -m pip install pywhatkit==5.4
python -m pip install openpyxl==3.1.2
python -m pip install ttkthemes==3.2.2
python -m pip install pillow==10.2.0

echo Cleaning previous build...
rmdir /s /q build
rmdir /s /q dist

echo Building executable...
python -m PyInstaller --clean ^
    --onefile ^
    --noconsole ^
    --name "The-Project" ^
    --add-data "customers.csv;." ^
    --add-data "backups;backups" ^
    --add-data "customer_files;customer_files" ^
    --add-data "logs;logs" ^
    --hidden-import customtkinter ^
    --hidden-import tkcalendar ^
    --hidden-import pywhatkit ^
    --hidden-import openpyxl ^
    --hidden-import ttkthemes ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    The-Project.py

echo Done! The executable is in the dist folder.
pause 