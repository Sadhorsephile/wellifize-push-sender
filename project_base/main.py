from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from integrations.redis import connections as redis_connections

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan actions:
    - Close Redis connections.
    """
    yield

    for con in redis_connections:
        con.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix='/api')
