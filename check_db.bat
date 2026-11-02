@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo       CampusLend - Database Verification Check
echo =========================================================
echo.

set MONGOSH="C:\mongosh-2.14.1-win32-x64\bin\mongosh.exe"
set OUT_FILE=%~dp0db_check_result.txt

if not exist %MONGOSH% (
    echo [!] mongosh.exe not found at %MONGOSH%
    pause
    exit /b 1
)

echo [*] Querying MongoDB at localhost:27017...
echo.

%MONGOSH% "mongodb://localhost:27017/campuslend_db" --quiet --eval "print('=== Available Databases ==='); db.getMongo().getDBNames().forEach(d => print('  * ' + d)); print('\n=== Collections in campuslend_db ==='); db.getCollectionNames().forEach(c => print('  * ' + c + ': ' + db[c].countDocuments() + ' records')); print('\n=== Verification Result ==='); if (db.getMongo().getDBNames().includes('campuslend_db')) { print('SUCCESS: campuslend_db exists!'); } else { print('NOT FOUND: campuslend_db does not exist yet.'); }" > "%OUT_FILE%" 2>&1

type "%OUT_FILE%"

echo.
echo =========================================================
pause

