@echo off
setlocal
cd /d "%~dp0"
echo =============================================================================
echo ZOE HOSPITAL EDITION (WINDOWS 7 SP1 COMPATIBLE - SIMULATED / NON-CLINICAL)
echo STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL OR PATIENT-CARE USE
echo =============================================================================

py -3 -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,7) else 1)" >nul 2>&1
if %errorlevel%==0 (
    py -3 "%~dp0zoe_hospital_win7.py" %*
    goto :eof
)

python -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,7) else 1)" >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0zoe_hospital_win7.py" %*
    goto :eof
)

if exist "%SystemRoot%\System32\mshta.exe" (
    echo Python 3.7+ not found. Launching native Windows 7 HTA kiosk via mshta.exe...
    start "" "%SystemRoot%\System32\mshta.exe" "%~dp0zoe_hospital_kiosk.hta"
    goto :eof
)

echo Launching offline HTML kiosk in default browser...
start "" "%~dp0zoe_hospital_kiosk.html"
