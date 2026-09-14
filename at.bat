@echo off
REM agent-tools launcher for Windows
REM Usage: at <category> <command> [args...]
cd /d "%~dp0.."
python -m agent_tools %*