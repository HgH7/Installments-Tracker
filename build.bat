@echo off
echo Installing required packages...
pip install --upgrade pip
pip install pyinstaller
pip install customtkinter==5.2.0
pip install tkcalendar==1.6.1
pip install pywhatkit==5.4
pip install openpyxl==3.1.2
pip install ttkthemes==3.2.2
pip install pillow==10.2.0

echo Cleaning previous build...
rmdir /s /q build
rmdir /s /q dist

echo Building executable...
pyinstaller --clean --onefile --noconsole ^
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
    --hidden-import datetime ^
    --hidden-import logging ^
    --hidden-import re ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import time ^
    --hidden-import threading ^
    --hidden-import json ^
    --hidden-import csv ^
    --hidden-import calendar ^
    --hidden-import webbrowser ^
    The-Project.py

echo Done! The executable is in the dist folder.
pause 