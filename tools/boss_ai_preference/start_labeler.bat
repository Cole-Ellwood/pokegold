@echo off
REM Boss AI Preference Labeler — one-click launcher.
REM Double-click this file to start the labeler server and open the
REM browser. Ctrl-C in the launched cmd window stops the server.
REM
REM Server URL: http://127.0.0.1:8765
REM Fixtures:   tools\boss_ai_preference\fixtures\boss_ai_preference_fixtures.json
REM Labels:     tools\boss_ai_preference\labels\boss_ai_pairwise_preferences.jsonl
REM
REM After labeling, see disagreement rate with:
REM   python -m tools.boss_ai_debugger regress

setlocal

REM cd to repo root (this file lives at tools\boss_ai_preference\, so up two)
cd /d "%~dp0..\..\"

echo.
echo  Boss AI Preference Labeler
echo  ==========================
echo   URL:  http://127.0.0.1:8765
echo   Stop: Ctrl-C in this window
echo.
echo  Browser opens in ~2 seconds.
echo.

REM Open the browser shortly after the server binds. The helper cmd is
REM minimized so it doesn't steal focus.
start "" /min cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8765"

REM Run the server in the foreground so logs are visible and Ctrl-C works.
python -m tools.boss_ai_preference serve --host 127.0.0.1 --port 8765

echo.
echo  Server stopped. Press any key to close this window.
pause >nul

endlocal
