import bcrypt

from app.domain.services.password_hasher import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):

    def hash(self, plaintext: str) -> str:
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt(rounds=12)).decode()

    def verify(self, plaintext: str, hashed: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
