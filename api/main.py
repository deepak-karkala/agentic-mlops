from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Simple root endpoint for health checks."""
    return {"message": "Agentic MLOps API"}
