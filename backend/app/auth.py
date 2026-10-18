import secrets

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from app.config import API_KEY

PUBLIC_PATHS = {"/health"}
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    request: Request, supplied: str | None = Security(api_key_header)
) -> None:
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return
    if not supplied or not secrets.compare_digest(supplied.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")