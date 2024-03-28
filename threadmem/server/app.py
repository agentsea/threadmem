import logging.config
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)

app = FastAPI()

access_logger = logging.getLogger("access")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    access_logger.info(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    access_logger.info(
        f"Returned response {request.method} {request.url}: {response.status_code}"
    )
    return response


def load_cors_origins() -> list:
    cors_origins_str = os.getenv("CORS_ORIGINS", "*")
    return cors_origins_str.split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=load_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Agent in the shell"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
