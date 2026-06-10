from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse


class AuthService:
    def register(self, db: Session, data: UserRegister) -> TokenResponse:
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        return TokenResponse(access_token=token)

    def login(self, db: Session, data: UserLogin) -> TokenResponse:
        user = db.query(User).filter(User.username == data.username).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        return TokenResponse(access_token=token)

    def get_me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
