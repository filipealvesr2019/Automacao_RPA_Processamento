@echo off
chcp 65001 > nul
title Servidor Local - Nexus ERP (RPA Target)
echo ======================================================
echo    NEXUS ERP CORPORATIVO - SERVIDOR LOCAL (RPA TARGET)
echo ======================================================
echo.
echo Iniciando servidor HTTP na porta 8080...
echo Abrindo navegador em http://localhost:8080
echo.
echo Pressione Ctrl + C nesta janela para encerrar o servidor.
echo ------------------------------------------------------

start http://localhost:8080
python server.py

