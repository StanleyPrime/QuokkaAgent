@echo off
REM ============= 确保在脚本所在目录 =============
cd /d "%~dp0"

REM ============= 进入 server 子目录 =============
cd server

REM ============= 并行启动所有后端服务 ============
start "AMAP Server"       cmd /k python amap_server.py
start "Bilibili Server"   cmd /k python bilibili_server.py
start "CodeExec Server"   cmd /k python code_executed_server.py
start "CMC Server"        cmd /k python CoinMarketCap_server.py
start "Draw Server"       cmd /k python Draw_server.py
start "FS Server"         cmd /k python file_system_server.py
start "GoogleMap Server"  cmd /k python googlemap_server.py
start "ScrapVid Server"   cmd /k python ScrapVedio_server.py
start "StreamlitSrv"      cmd /k python streamlitServer.py
start "WebSearch Server"  cmd /k python WebSearch_server.py
start "YouTube Server"    cmd /k python youtube_server.py
start "Video_Processing_server"    cmd /k python Video_Processing_server.py
start "mornitor_server"    cmd /k python mornitor_server.py

REM ============= 回到项目根目录 =============
cd /d "%~dp0"

REM ============= 启动 Streamlit 前端 ============
start "Streamlit UI"      cmd /k streamlit run client.py

exit /b
