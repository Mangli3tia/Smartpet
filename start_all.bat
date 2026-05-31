@echo off
setlocal enabledelayedexpansion

REM 获取批处理文件所在目录（项目根目录）
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM 设置 conda 环境的 Python 路径（请根据实际情况修改下面一行）
set "CONDA_PYTHON=D:\APP\Program\Anaconda\envs\MQTT\python.exe"

REM 检查该路径是否存在
if not exist "%CONDA_PYTHON%" (
    echo Error: Cannot find Python at %CONDA_PYTHON%
    echo Please update the CONDA_PYTHON path in this script.
    pause
    exit /b 1
)

REM 启动三个窗口，每个窗口先 cd 到项目目录，再运行对应的 Python 脚本
start "Subscriber" cmd /k "cd /d "%PROJECT_DIR%" && "%CONDA_PYTHON%" subscriber.py"
start "Web Server" cmd /k "cd /d "%PROJECT_DIR%" && "%CONDA_PYTHON%" web_server.py"
start "Publisher" cmd /k "cd /d "%PROJECT_DIR%" && "%CONDA_PYTHON%" publisher.py"

REM 等待服务启动
timeout /t 3 /nobreak >nul

REM 打开浏览器
start http://127.0.0.1:5000

echo All services started. Close each terminal window to stop.
pause