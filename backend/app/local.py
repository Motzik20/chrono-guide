import uvicorn
from fastapi import FastAPI

from app import env


def _create_app() -> FastAPI:
    from app.main import app as fastapi_app

    return fastapi_app


env.create_local_config()
app = _create_app()

if __name__ == "__main__":
    uvicorn.run("local:app", host="0.0.0.0", port=8000, reload=True)
