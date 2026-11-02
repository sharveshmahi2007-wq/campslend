@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo      CampusLend / LendLoop - MongoDB Database Creator
echo =========================================================
echo.

set DB_SCRIPT=%~dp0backend\src\main\resources\data\init_database.js

:: 1. Primary check: Custom user location for mongosh
if exist "C:\mongosh-2.14.1-win32-x64\bin\mongosh.exe" (
    echo [*] Found mongosh at C:\mongosh-2.14.1-win32-x64\bin\mongosh.exe
    echo [*] Running database seed script against mongodb://localhost:27017/campuslend_db ...
    echo.
    "C:\mongosh-2.14.1-win32-x64\bin\mongosh.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
    goto :done
)

:: 2. Check any mongosh version in root C:\
for /d %%D in ("C:\mongosh-*\bin") do (
    if exist "%%D\mongosh.exe" (
        echo [*] Found mongosh at %%D\mongosh.exe
        echo [*] Running database seed script...
        echo.
        "%%D\mongosh.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
        goto :done
    )
)

:: 3. Check if mongosh is available in PATH
where mongosh >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [*] Found mongosh in PATH. Running database seed script...
    mongosh "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
    goto :done
)

:: 4. Check standard MongoDB bin directory for mongosh
for /d %%D in ("C:\Program Files\MongoDB\Server\*") do (
    if exist "%%D\bin\mongosh.exe" (
        echo [*] Found mongosh at %%D\bin\mongosh.exe. Running seed script...
        "%%D\bin\mongosh.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
        goto :done
    )
    if exist "%%D\bin\mongo.exe" (
        echo [*] Found legacy mongo shell at %%D\bin\mongo.exe. Running seed script...
        "%%D\bin\mongo.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
        goto :done
    )
)

:: 5. Check for standalone mongosh in AppData
if exist "%LOCALAPPDATA%\Programs\mongosh\mongosh.exe" (
    echo [*] Found mongosh in user directory. Running seed script...
    "%LOCALAPPDATA%\Programs\mongosh\mongosh.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
    goto :done
)

echo [!] Could not find 'mongosh.exe' automatically.
echo.
echo You can run the database script manually:
echo    "C:\mongosh-2.14.1-win32-x64\bin\mongosh.exe" "mongodb://localhost:27017/campuslend_db" "%DB_SCRIPT%"
echo.

:done
echo.
pause
