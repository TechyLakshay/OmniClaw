@echo off
cd /d C:\Users\laksh\Desktop\side-projects\mini-claw
python -m uvicorn app.web.app:app --reload --port 8000
