@echo off
call %~dp0%vars.bat
set sitedir=%WPYDIR%\python-3.8.10.amd64\Lib\site-packages
REM ~ type %sitedir%\openstack\config\defaults.json
REM ~ goto :DONE
rd/s/q build
rd/s/q dist
del urotc.spec

@echo on
pyinstaller --onefile ^
  --hidden-import keystoneauth1 ^
  --collect-data keystoneauth1 ^
  --copy-metadata keystoneauth1 ^
  --hidden-import os_service_types ^
  --collect-data os_service_types ^
  --copy-metadata os_service_types ^
  --collect-all openstacksdk ^
  --copy-metadata openstacksdk ^
  --add-data %sitedir%\openstack\config\defaults.json;openstack\config ^
  --hidden-import keystoneauth1.loading._plugins ^
  --hidden-import keystoneauth1.loading._plugins.identity ^
  --hidden-import keystoneauth1.loading._plugins.identity.generic ^
  urotc.py
@echo off
REM ~ --hidden-import MODULENAME, --hiddenimport MODULENAME
REM ~ --collect-submodules MODULENAME
REM ~ --collect-data MODULENAME, --collect-datas MODULENAME
REM ~ --collect-binaries MODULENAME
REM ~ --collect-all MODULENAME
REM ~ --copy-metadata PACKAGENAME
REM ~ --recursive-copy-metadata PACKAGENAME

REM ~ --hidden-import=pytorch
REM ~ --collect-data torch
REM ~ --copy-metadata torch
REM ~ --copy-metadata tqdm
REM ~ --copy-metadata regex
REM ~ --copy-metadata sacremoses
REM ~ --copy-metadata requests
REM ~ --copy-metadata packaging
REM ~ --copy-metadata filelock
REM ~ --copy-metadata numpy
REM ~ --copy-metadata tokenizers
REM ~ --copy-metadata importlib_metadata
REM ~ --hidden-import="sklearn.utils._cython_blas"
REM ~ --hidden-import="sklearn.neighbors.typedefs"
REM ~ --hidden-import="sklearn.neighbors.quad_tree"
REM ~ --hidden-import="sklearn.tree"
REM ~ --hidden-import="sklearn.tree._utils"

:DONE
