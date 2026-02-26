from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Annotated
from .config import settings
from .exceptions import VedFinException
import structlog

logger = structlog.get_logger()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

class UnauthorizedException(VedFinException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type_uri="https://vedfin.com/errors/unauthorized",
            title="Unauthorized",
            detail=detail
        )

async def verify_jwt_token(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Validates JWT token against SECRET_KEY.
    Returns decoded payload if valid, raises RFC 7807 exception if invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise UnauthorizedException(detail="Subject missing in token")
        return payload
    except JWTError as e:
        logger.warning("invalid_token_attempt", error=str(e))
        raise UnauthorizedException(detail="Invalid or expired token")

# Explicit dependency type alias for reuse
VerifiedToken = Annotated[dict, Depends(verify_jwt_token)]
