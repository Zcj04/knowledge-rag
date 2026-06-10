from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class UserPreferenceUpdate(BaseModel):
    key: str
    value: dict


class UserPreferenceResponse(BaseModel):
    key: str
    value: dict

    model_config = {"from_attributes": True}
