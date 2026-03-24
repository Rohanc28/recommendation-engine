@echo off
echo Starting project...

REM -------- BACKEND --------
start cmd /k ^
"cd backend && ^
copy .env.example .env && ^
pip install -r requirements.txt && ^
alembic upgrade head && ^
uvicorn app.main:app --reload"

REM -------- FRONTEND --------
start cmd /k ^
"cd frontend && ^
npm install && ^
npm run dev"

echo All services started!
pause
