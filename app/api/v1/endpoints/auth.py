from typing import Optional

from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


async def get_admin_secret(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    authorization: Optional[str] = Header(None),
) -> str:
    # Prefer Swagger/OpenAPI security credentials when available.
    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        return credentials.credentials

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Fallback keeps compatibility for manual raw header clients.
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use: Bearer <secret_key>",
        )

    return parts[1]