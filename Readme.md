# Realtime Youtube Live Message Analysis
Analyse the live chat messages from a live youtube video and display in a custom react frontend.

## Tech Stack

<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-plain-wordmark.svg" height=100 /><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/apachekafka/apachekafka-original-wordmark.svg" height=100 /><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mongodb/mongodb-original.svg" height=100 /><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" height=100 />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original-wordmark.svg" height=100 />
          
         

## Architecture

!['Architecture Diagram'](/assets/Diagram.png)

## Directory Structure Basic Overview
```python
client/
│ ├─backend/    # Backend Code For API and SSE
│ │ ├─app.py
│ │ ├─example.env
│ │ └─settings.py
│ └─frontend/               
│   └─chat-tracker/ #React FontEnd
│     ├─.gitignore
│     ├─index.html
│     ├─node_modules/
│     ├─package-lock.json
│     ├─package.json
│     ├─postcss.config.js
│     ├─public/
│     ├─src/    # FrontEnd Code
│     ├─tailwind.config.js
│     └─vite.config.js
├─docker/
│ ├─kafka/
│    └─docker-compose.yml  # Docker Compose to Run Kafka
│
├─init.bat # Script to Start all bat files at once
├─pipeline/
│ ├─load/   # Loader Module to push data to mongodb
│ │ ├─example.env
│ │ ├─loader.log
│ │ ├─mongoload.py
│ │ ├─settings.py
│ │ └─__init__.py
│ ├─process/ # Process Module to do analysis like sentiment
│ │ ├─analysis.py
│ │ ├─example.env
│ │ ├─exceptions.py
│ │ ├─models.py
│ │ ├─process.log
│ │ └─settings.py
│ └─scraper/ # Scraper module to scraper data and push to topic
│   ├─exceptions.py
│   ├─live.log
│   ├─live.py
│   ├─example.env  # Env file to store environment variables
│   ├─models.py
│   ├─settings.py
├─Readme.md
├─requirements.txt
└─run_client.bat    # Script to run the frontend client
└─run_loader.bat    # Script to start loader module to push to db
└─run_process.bat   # Script to start process module for analysis
└─run_scraper.bat   # Script to start scraper with a URL prompt
└─run_server.bat # Script to start backend API and SSE Server

```

# Basic Setup Instructions

## For Windows
- Clone Repo
- Have a existing runnning kafka or setup one using the docker compose from `docker/kafka`
- Create a ``main.env`` for every `example.env` in every directory like , `backend` , `load`,`process`,`scraper` and fill your settings.
- Run `init.bat` from cmd to start all services.
- In terminal titles scraper a prompt will be asked to enter live video url add. Choose any live video with chat enabled to start the tracking.




## Demo

https://youtu.be/RPR3K9yUDVM


## Current Limitations
- Frontend tracks only one video.
- Have to spin up multiple scraper for multiple urls.





