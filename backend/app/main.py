from fastapi import FastAPI

import app.app_factory as app_factory
import app.env as env


def _init() -> FastAPI:
    app = app_factory.create_app(local=env.is_local_env())
    return app


app = _init()
