@echo off
echo Creating distribution package...

:: Create distribution folder
if exist "Installments Manager" rmdir /s /q "Installments Manager"
mkdir "Installments Manager"

:: Copy executable and its dependencies
echo Copying executable...
xcopy /E /I /Y "dist\Installments Manager\*" "Installments Manager\"

:: Copy data folders (create empty ones)
echo Creating data folders...
mkdir "Installments Manager\customer_files"
mkdir "Installments Manager\backups"
mkdir "Installments Manager\logs"

:: Copy empty data files
echo Creating data files...
echo Name,Phone,Amount,Installments,Start Date,Installment Dates,Paid Installments> "Installments Manager\customers.csv"
echo.> "Installments Manager\PyWhatKit_DB.txt"

:: Create README
echo Creating README...
(
echo # Installments Manager
echo.
echo This is a standalone application for managing customer installments.
echo.
echo ## Contents
echo - Installments Manager.exe: Main application executable
echo - customer_files/: Directory for customer-related files
echo - backups/: Directory containing backup files
echo - logs/: Directory containing application logs
echo - customers.csv: Customer database
echo - PyWhatKit_DB.txt: WhatsApp integration database
echo.
echo ## Usage
echo 1. Double-click Installments Manager.exe to start the application
echo 2. All data will be automatically saved in the respective folders
echo 3. Backups are created automatically
) > "Installments Manager\README.md"

echo.
echo Distribution package created successfully!
echo Location: Installments Manager
echo.
pause 