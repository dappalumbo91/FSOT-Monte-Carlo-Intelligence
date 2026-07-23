@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Stop FSOT Monte Carlo Intelligence

set "PORT=8765"
echo.
echo  Stopping FSOT server on port %PORT% ...
echo.

powershell -NoProfile -Command ^
  "$conns = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; ^
   if (-not $conns) { Write-Host 'Nothing listening on port %PORT%.'; exit 0 }; ^
   $pids = @($conns | Select-Object -ExpandProperty OwningProcess -Unique); ^
   foreach ($p in $pids) { ^
     try { ^
       $proc = Get-Process -Id $p -ErrorAction Stop; ^
       Write-Host (\"Stopping PID {0} ({1})\" -f $p, $proc.ProcessName); ^
       Stop-Process -Id $p -Force -ErrorAction Stop; ^
     } catch { Write-Host (\"Could not stop PID {0}: {1}\" -f $p, $_.Exception.Message) } ^
   }; ^
   Start-Sleep -Seconds 1; ^
   $left = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; ^
   if ($left) { Write-Host 'WARNING: port still in use.' } else { Write-Host 'Done. Port is free.' }"

echo.
pause
exit /b 0
