@echo off
REM ============= 确保在脚本所在目录 =============
cd /d "%~dp0"

REM ============= 进入 server 子目录 =============
cd server

REM ============= 并行启动所有后端服务（/B 表示不新开窗口，在同一控制台中后台运行） ============
start "AMAP Server"  /B python amap_server.py
start "Bilibili Server"  /B python bilibili_server.py
start "CodeExec Server"  /B python code_executed_server.py
start "CMC Server"  /B python CoinMarketCap_server.py
start "Draw Server"  /B python Draw_server.py
start "FS Server"  /B python file_system_server.py
start "GoogleMap Server"  /B python googlemap_server.py
start "ScrapVid Server"  /B python ScrapVedio_server.py
start "StreamlitSrv"  /B python streamlitServer.py
start "WebSearch Server"  /B python WebSearch_server.py
start "YouTube Server"  /B python youtube_server.py
start "Video_Processing_server"  /B python Video_Processing_server.py
start "mornitor_server"  /B python mornitor_server.py

REM ============= 回到项目根目录 =============
cd /d "%~dp0"

REM ============= 启动 Streamlit 前端（同样在当前窗口后台运行） ============
start "Streamlit UI"  /B streamlit run client.py

REM ============= 提示并保持窗口打开 ============
echo.
echo =============================================
echo all server has started.
echo press any key to exit.
echo =============================================
pause >nul
