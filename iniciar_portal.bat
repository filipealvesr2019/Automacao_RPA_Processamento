@echo off
chcp 65001 > nul
title Servidor Local - Nexus ERP (RPA Target)
echo ======================================================
echo    NEXUS ERP CORPORATIVO - SERVIDOR LOCAL (RPA TARGET)
echo ======================================================
echo.
echo Iniciando servidor HTTP na porta 8000...
echo Abrindo navegador em http://localhost:8000
echo.
echo Pressione Ctrl + C nesta janela para encerrar o servidor.
echo ------------------------------------------------------

start http://localhost:8000
python -m http.server 8000 --directory PortalWeb

