from fastapi import FastAPI,Request
from pymongo import MongoClient
import settings
import uvicorn
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print('Connecting to MongoDB:',settings.MONGO_URL)

client = MongoClient(settings.MONGO_URL)
db = client.main
message_collection = db.live
info_collection=db.info 


async def read_stream():
    change_stream = message_collection.watch()
    while True:
        for change in change_stream:
            if change['operationType']=='insert':
                doc=change['fullDocument']
                doc.pop('_id')
                response={"data":doc,"event":"message"}
                yield response
            





@app.get("/stream")
async def stream_changes(request:Request):
    
    return EventSourceResponse(read_stream())


@app.get("/video/{video_id}")
async def get_video(video_id: str):
    filter = {"video_id": video_id}
    result = info_collection.find_one(filter)
    result.pop('_id')
    return result




@app.on_event("shutdown")
async def shutdown_event():
    client.close()


if __name__=='__main__':
    uvicorn.run("app:app",port=3000,reload=True)