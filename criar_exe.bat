@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)

echo Instalando dependencias...
%PY% -m pip install pyinstaller pynput
if errorlevel 1 goto erro

echo.
echo Fechando o Roube um Ovo, se estiver aberto...
taskkill /f /im "Roube um Ovo.exe" >nul 2>nul
timeout /t 2 /nobreak >nul

if exist "dist\Roube um Ovo.exe" del /f /q "dist\Roube um Ovo.exe"
if exist "dist\Roube um Ovo.exe" (
    echo.
    echo Nao foi possivel apagar o "Roube um Ovo.exe" antigo. Ele ainda esta em uso.
    echo Feche o programa e qualquer janela da pasta dist, e tente de novo.
    echo Se continuar, pause o antivirus por alguns minutos ou adicione esta pasta as excecoes.
    goto erro_simples
)

echo.
echo Gerando o programa (pode levar 1 a 2 minutos)...
set ICONE=
if exist "%~dp0icone.ico" set ICONE=--icon "%~dp0icone.ico"
%PY% -m PyInstaller --onefile --noconsole --clean --noconfirm %ICONE% --name "Roube um Ovo" ovo_macro.py
if errorlevel 1 goto erro

echo.
echo Pronto! O programa esta em:
echo %~dp0dist\Roube um Ovo.exe
echo.
echo Copie o arquivo "Roube um Ovo.exe" para a area de trabalho.
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Copie a mensagem acima e envie para o Claude.
echo Se a mensagem for "Acesso negado", feche o Roube um Ovo e o antivirus e tente de novo.
pause
exit /b 1

:erro_simples
pause
exit /b 1
