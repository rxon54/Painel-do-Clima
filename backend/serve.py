from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve data files (JSON, etc.) first!
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
app.mount("/data", StaticFiles(directory=data_dir), name="data")

# Serve frontend static files (catch-all)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
