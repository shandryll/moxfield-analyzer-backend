import os
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    status = getattr(exc, "status_code", 500)
    logger.error("Unhandled exception", status=status, error=str(exc), path=str(request.url))

    if os.getenv("ENVIRONMENT", "development") == "development":
        detail = str(exc)
    else:
        detail = "Internal server error"

    return JSONResponse(
        status_code=status,
        content={"error": detail},
    )
