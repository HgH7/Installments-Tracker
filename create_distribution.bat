@echo off
echo Creating distribution package...

:: Create distribution folder
if exist "Installments-Tracker-Distribution" (
    echo Removing old distribution folder...
    rmdir /s /q "Installments-Tracker-Distribution"
)
mkdir "Installments-Tracker-Distribution"

:: Copy executable
echo Copying executable...
copy "dist\Installments-Tracker.exe" "Installments-Tracker-Distribution\"

:: Copy data files
echo Copying data files...
copy "customers.csv" "Installments-Tracker-Distribution\"
copy "PyWhatKit_DB.txt" "Installments-Tracker-Distribution\"

:: Copy folders
echo Copying folders...
xcopy /E /I "customer_files" "Installments-Tracker-Distribution\customer_files"
xcopy /E /I "backups" "Installments-Tracker-Distribution\backups"
xcopy /E /I "logs" "Installments-Tracker-Distribution\logs"

:: Create README
echo Creating README file...
(
echo Installments Tracker - Installation Instructions
echo.
echo 1. Extract all files to a folder of your choice
echo 2. Double-click Installments-Tracker.exe to run the program
echo 3. The program will create necessary folders automatically
echo.
echo Important Notes:
echo - Keep all files in the same folder
echo - Do not delete any of the included folders
echo - The program will create backups automatically
echo - Customer files are stored in the customer_files folder
echo - Logs are stored in the logs folder
) > "Installments-Tracker-Distribution\README.txt"

:: Create zip file
echo Creating zip file...
powershell Compress-Archive -Path "Installments-Tracker-Distribution" -DestinationPath "Installments-Tracker-Distribution.zip" -Force

echo.
echo Distribution package created successfully!
echo The zip file is: Installments-Tracker-Distribution.zip
echo.
pause 