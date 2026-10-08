
REM Verificar Python
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python no encontrado
    echo Descarga Python desde: https://www.python.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Verificar Node.js
echo [2/5] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Node.js no encontrado
    echo Descarga Node.js desde: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js encontrado

REM Backend
echo [3/5] Instalando dependencias backend...
cd backend
python -m venv venv_new
call venv_new\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
cd..

REM Frontend
echo [4/5] Instalando dependencias frontend...
cd frontend
call npm install
cd..
