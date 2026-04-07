from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.domain.services.jwt_service import IJwtService

_ALGORITHM = "HS256"


class JoseJwtService(IJwtService):

    def __init__(self, secret_key: str, access_token_expire_minutes: int) -> None:
        self._secret = secret_key
        self._expire_minutes = access_token_expire_minutes

    def create_access_token(self, user_id: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def decode_access_token(self, token: str) -> dict:
        payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("Not an access token")
        return payload
