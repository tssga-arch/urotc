@echo off
call %~dp0%cfg.bat

if not exist %~dp0dist\urotc\urotc.exe goto :is_not_dir
  %~dp0dist\urotc\urotc.exe %*
  goto :DONE
:is_not_dir
if not exist %~dp0dist\urotc.exe goto :is_not_exe
  %~dp0dist\urotc.exe %*
  goto :DONE
:is_not_exe
echo Missing pydist file.  Run MK.BAT

:DONE
set TOKEN_ID=
set TOKEN_PSK=
set PROJECT=
set DOMAIN=
set AUTH_URL=
set RESOURCE_ID=
