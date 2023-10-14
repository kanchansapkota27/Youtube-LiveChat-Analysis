@echo off

:: Activate the virtualenv 
call venv/Scripts/activate.bat

:: Change to the scripts directory
cd pipeline\load

:: Set title
title Loader

:: Run the Python script
python mongoload.py

:: Keep virtualenv activated after running
:: call %venvPath%\Scripts\deactivate.bat