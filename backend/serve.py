from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

app = FastAPI(title="Painel do Clima", description="Climate data visualization for Brazilian municipalities")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Painel do Clima"}

if __name__ == "__main__":
    print("Starting Painel do Clima server...")
    print("Frontend: http://localhost:8000")
    print("Data API: http://localhost:8000/data")
    print("Health check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
