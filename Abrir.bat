@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3.10 ou mais novo em python.org e marque "Add to PATH".
  pause
  exit /b 1
)
python -c "import pynput" >nul 2>nul
if errorlevel 1 (
  echo Instalando o pynput, so na primeira vez...
  python -m pip install pynput
)
python -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo Instalando o Pillow, so na primeira vez...
  python -m pip install pillow
)
python -c "import imageio_ffmpeg" >nul 2>nul
if errorlevel 1 (
  echo Instalando o componente de video do clipe, so na primeira vez...
  python -m pip install imageio-ffmpeg
)
start "" pythonw ovo_macro.py
