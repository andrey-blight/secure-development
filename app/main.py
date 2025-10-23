from fastapi import FastAPI

from .api import router as api_router
from .api.middleware import CorrelationIdMiddleware, setup_exception_handlers

app = FastAPI(
    title="SecDev Course App",
    version="0.1.0",
    description="Secure Development Course Project with RFC 7807 error handling",
)

app.add_middleware(CorrelationIdMiddleware)

setup_exception_handlers(app)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router)
