from fastapi import FastAPI
from . import __version__

app = FastAPI(title="Sports Intelligence API", version=__version__)

@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "version": __version__}

@app.get("/v1/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "execution_boundary": "analysis_only"}

@app.get("/v1/models")
def models() -> dict[str, list]:
    return {"models": []}

@app.get("/v1/events")
def events() -> dict[str, list]:
    return {"events": []}
