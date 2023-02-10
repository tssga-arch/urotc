@echo off
set urotc=%~dp0%urotc.py
call %~dp0%vars.bat
call %~dp0%cfg.bat

python %urotc% %*

:DONE
set TOKEN_ID=
set TOKEN_PSK=
set PROJECT=
set DOMAIN=
set AUTH_URL=
set RESOURCE_ID=
