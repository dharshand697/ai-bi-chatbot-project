@echo off
title InsightAI Backend Server
echo ================================================
echo   InsightAI Backend Server
echo ================================================
echo   URL: http://127.0.0.1:8000
echo   Health: http://127.0.0.1:8000/health
echo   Close this window to stop the server
echo ================================================

cd /d "C:\Users\manya\Downloads\ai-bi-chatbot-project"

:start
python -c "import uvicorn; uvicorn.run('api.main:app', host='127.0.0.1', port=8000, reload=False, log_level='info')"

echo.
echo Server stopped. Restarting in 3 seconds...
timeout /t 3
goto start
