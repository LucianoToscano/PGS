@echo off
setlocal
if defined PGS_PYTHON (
  "%PGS_PYTHON%" "%~dp0pgs.cmd" %*
  exit /b %errorlevel%
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0pgs.cmd" %*
) else (
  python "%~dp0pgs.cmd" %*
)
exit /b %errorlevel%
