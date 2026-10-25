@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo NEXUS - One Click Launcher
echo ============================================

docker --version >nul 2>&1
if errorlevel 1 (
  echo Docker is not installed or not available in PATH.
  echo Start Docker Desktop and run this file again.
  pause
  exit /b 1
)

echo.
echo Starting NEXUS containers...
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo NEXUS failed to start. Run: docker compose logs --tail=100
  pause
  exit /b 1
)

echo.
echo Waiting for the backend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; 1..60 | %% { try { $r=Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true; break} } catch {}; Start-Sleep -Seconds 2 }; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo Backend is taking longer than expected. Containers are still running.
  echo Check: http://localhost:8000/health
) else (
  echo Backend is ready.
)

echo.
echo Opening NEXUS...
start "" "http://localhost:3000/login"
echo Swagger: http://localhost:8000/docs
echo Project: http://localhost:3000/project/1

echo.
echo NEXUS is running. Keep Docker Desktop open.
pause
endlocal
