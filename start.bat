@echo off
echo.
echo  ====================================================
echo   AgriGuard - Starting Server...
echo  ====================================================
echo.
echo  Open your browser at: http://127.0.0.1:8000
echo  Press CTRL+C to stop the server.
echo.
call venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
