from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI()

# Serve everything in the current directory (including visu_2.html and data/)
app.mount("/", StaticFiles(directory=os.path.dirname(__file__), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("serve:app", host="127.0.0.1", port=8009, reload=True)
