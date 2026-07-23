@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title FSOT Monte Carlo Intelligence

set "PORT=8765"
set "URL=http://127.0.0.1:%PORT%/"
set "PYTHONPATH=%CD%"
set "FSOT_MC_QWEN_LOAD=4bit"
set "FSOT_MC_QWEN_MAX_INPUT=2800"
set "FSOT_MC_QWEN_WARM=1"

echo.
echo  ============================================
echo   FSOT Monte Carlo Intelligence
echo  ============================================
echo   UI:  %URL%
echo   Close this window or Ctrl+C to stop.
echo  ============================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
  set "PY=%~dp0.venv\Scripts\python.exe"
  echo Using venv Python: .venv\Scripts\python.exe
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo ERROR: No .venv found and no "python" on PATH.
    echo Install Python 3.11+, then:  python -m venv .venv
    echo   .\.venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    echo   pip install torch --index-url https://download.pytorch.org/whl/cu128
    echo   pip install -e ".[narrate]"
    pause
    exit /b 1
  )
  set "PY=python"
  echo Using system Python on PATH
)

REM Chat needs torch in this same Python (UI still works without it).
"%PY%" -c "import torch" >nul 2>&1
if errorlevel 1 (
  echo.
  echo WARNING: torch not installed in this Python — chat/Qwen will not load.
  echo Fix once ^(CUDA 12.8 wheel^):
  echo   "%PY%" -m pip install torch --index-url https://download.pytorch.org/whl/cu128
  echo   "%PY%" -m pip install -e ".[narrate]"
  echo UI graph still works; only "Talk to the work" needs torch.
  echo.
) else (
  echo torch OK for Qwen chat
)

REM Already up? Just open the browser.
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% equ 0 (
  echo Server already running on port %PORT% — opening browser.
  start "" "%URL%"
  echo.
  echo Leave the other console open while you use the UI.
  pause
  exit /b 0
)

REM Open the browser once /api/health responds (up to ~90s).
start "FSOT open browser" /min cmd /c "powershell -NoProfile -Command \"$ok=$false; for($i=0;$i -lt 90;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 2; if($r.StatusCode -eq 200){ $ok=$true; break } } catch {} Start-Sleep -Seconds 1 }; if($ok){ Start-Process '%URL%' } else { [Console]::Error.WriteLine('Timed out waiting for server on port %PORT%.') }\""

echo Starting server on port %PORT% ...
echo.
"%PY%" -m fsot_mc serve --port %PORT%
set "EC=%ERRORLEVEL%"
echo.
echo Server stopped ^(exit %EC%^).
pause
exit /b %EC%
