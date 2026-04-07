from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.application.dtos.auth_dto import LoginRequest as LoginDTO, RefreshTokenRequest, RegisterUserRequest
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.logout_user import LogoutUserUseCase
from app.application.use_cases.refresh_access_token import RefreshAccessTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.infrastructure.config import get_settings
from app.presentation.dependencies import (
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
    get_register_use_case,
)
from app.presentation.schemas.auth_schema import AccessTokenResponse, RegisterRequest, UserResponse

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        secure=settings.is_prod,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/auth",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> UserResponse:
    try:
        result = await use_case.execute(
            RegisterUserRequest(email=body.email, password=body.password)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return UserResponse(user_id=result.user_id, email=result.email)


@router.post("/login", response_model=AccessTokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,  # required by slowapi rate limiter
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: LoginUserUseCase = Depends(get_login_use_case),
) -> AccessTokenResponse:
    try:
        token_result, raw_refresh = await use_case.execute(
            LoginDTO(email=form.username, password=form.password)
        )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _set_refresh_cookie(response, raw_refresh)
    return AccessTokenResponse(access_token=token_result.access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    use_case: RefreshAccessTokenUseCase = Depends(get_refresh_use_case),
) -> AccessTokenResponse:
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        token_result, new_raw = await use_case.execute(RefreshTokenRequest(raw_token=raw_token))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    _set_refresh_cookie(response, new_raw)
    return AccessTokenResponse(access_token=token_result.access_token)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    use_case: LogoutUserUseCase = Depends(get_logout_use_case),
) -> None:
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if raw_token:
        await use_case.execute(raw_token)
    response.delete_cookie(key=_REFRESH_COOKIE, path="/auth")
