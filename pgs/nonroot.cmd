@echo off
rem Compatibility launcher: use pgs.cmd for new builds.
call "%~dp0pgs.cmd" %*
exit /b %errorlevel%
