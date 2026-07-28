@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title FSOT Monte Carlo Intelligence

set "PORT=8765"
if not "%FSOT_MC_PORT%"=="" set "PORT=%FSOT_MC_PORT%"
set "URL=http://127.0.0.1:%PORT%/"
set "PYTHONPATH=%CD%"
set "FSOT_MC_QWEN_LOAD=4bit"
set "FSOT_MC_QWEN_MAX_INPUT=2800"
if "%FSOT_MC_QWEN_WARM%"=="" set "FSOT_MC_QWEN_WARM=1"

REM Optional: force free port then start (START_FSOT.bat force)
set "FORCE=0"
if /I "%~1"=="force" set "FORCE=1"
if /I "%~1"=="--force" set "FORCE=1"
if /I "%~1"=="/force" set "FORCE=1"

echo.
echo  ============================================
echo   FSOT Monte Carlo Intelligence
echo  ============================================
echo   Folder: %CD%
echo   UI:     %URL%
echo   Close this window or Ctrl+C to stop.
echo   Restart later from UI:  Ctrl+Shift+R  or  Restart button
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

REM If this tree lives on a slow drive (e.g. I:), prefer Desktop model weights when present.
echo %CD%| findstr /I /B "I:" >nul
if not errorlevel 1 (
  echo.
  echo NOTE: Launching from I: drive — can be slow for first Qwen warm.
  if exist "C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence\vendor\models\Qwen2.5-7B-Instruct\config.json" (
    if "%FSOT_MC_QWEN_PATH%"=="" (
      set "FSOT_MC_QWEN_PATH=C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence\vendor\models\Qwen2.5-7B-Instruct"
      echo Using FAST Desktop Qwen weights for chat:
      echo   %FSOT_MC_QWEN_PATH%
    )
  ) else (
    echo WARNING: Qwen weights will load from I: — first warm can take several minutes.
  )
  echo.
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

if "%FORCE%"=="1" (
  echo FORCE: freeing port %PORT% ...
  call "%~dp0STOP_FSOT.bat" nopause
)

REM Port already in use?
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% equ 0 (
  echo.
  echo Port %PORT% already has a FSOT server answering /api/health.
  echo That may be the OTHER copy ^(Desktop vs I:^) — not necessarily this folder.
  echo.
  echo   [Enter] open browser to existing server
  echo   [F]     free port and start THIS folder
  echo   [Q]     quit
  choice /C FQ /N /M "Press F to force this folder, Q to quit, or close and just open browser with Enter cancelled - use F or Q: "
  if errorlevel 2 exit /b 0
  if errorlevel 1 (
    call "%~dp0STOP_FSOT.bat" nopause
    timeout /t 2 /nobreak >nul
  )
)

REM Open the browser once /api/health responds (longer wait if on I:).
set "WAIT_SECS=90"
echo %CD%| findstr /I /B "I:" >nul
if not errorlevel 1 set "WAIT_SECS=180"

start "FSOT open browser" /min cmd /c "powershell -NoProfile -Command \"$ok=$false; for($i=0;$i -lt %WAIT_SECS%;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 2; if($r.StatusCode -eq 200){ $ok=$true; break } } catch {} Start-Sleep -Seconds 1 }; if($ok){ Start-Process '%URL%' } else { [Console]::Error.WriteLine('Timed out waiting for server on port %PORT%.') }\""

echo Starting server from:
echo   %CD%
echo Port %PORT% ...
echo.
"%PY%" -m fsot_mc serve --port %PORT%
set "EC=%ERRORLEVEL%"
echo.
echo Server stopped ^(exit %EC%^).
pause
exit /b %EC%
