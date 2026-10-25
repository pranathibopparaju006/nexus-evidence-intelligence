@echo off
cd /d "%~dp0"
echo Stopping NEXUS...
docker compose down
echo NEXUS stopped.
pause
