TITLE Scraper
call venv/Scripts/activate.bat
cd pipeline/scraper
@REM python live.py --url https://www.youtube.com/watch?v=TPcmrPrygDc
@REM python live.py --url https://www.youtube.com/watch?v=YZ0QUd-URt4

:: Prompt user for URL input
set /p URL=Enter URL to scrape: 

:: Run script with user input URL
python live.py --url %URL%