from dataclasses import dataclass


@dataclass
class RegisterUserRequest:
    email: str
    password: str


@dataclass
class LoginRequest:
    email: str
    password: str


@dataclass
class UserCreatedResult:
    user_id: str
    email: str


@dataclass
class AuthTokenResult:
    access_token: str
    token_type: str
    user_id: str
    email: str


@dataclass
class AccessTokenResult:
    access_token: str
    token_type: str


@dataclass
class RefreshTokenRequest:
    raw_token: str
