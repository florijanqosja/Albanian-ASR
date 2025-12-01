import datetime as _dt
from typing import Optional, Generic, TypeVar, Any
import pydantic as _pydantic

T = TypeVar('T')

class ResponseModel(_pydantic.BaseModel, Generic[T]):
    status: str
    data: Optional[T] = None
    message: Optional[str] = None


class VideoBase(_pydantic.BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    category: Optional[str] = None
    to_mp3_status: Optional[str] = None
    splice_status: Optional[str] = None
    mp3_path: Optional[str] = None

class Video(VideoBase):
    id: int
    upload_time: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)

class VideoCreate(VideoBase):
    pass


class SpliceBase(_pydantic.BaseModel):
    name: str
    path: str
    label: str
    origin: str
    duration: str
    validation: str
    owner_id: str


class Splice(SpliceBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class SpliceCreate(SpliceBase):
    pass


class LabeledSpliceBase(_pydantic.BaseModel):
    name: str
    path: str
    label: str
    origin: str
    duration: str
    validation: str
    owner_id: str
    labeler_id: Optional[str] = None


class LabeledSplice(LabeledSpliceBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class LabeledSpliceCreate(LabeledSpliceBase):
    pass


class HighQualityLabeledSpliceBase(_pydantic.BaseModel):
    name: str
    path: str
    label: str
    origin: str
    duration: str
    validation: str
    owner_id: str
    validator_id: str
    labeler_id: Optional[str] = None


class HighQualityLabeledSplice(HighQualityLabeledSpliceBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class HighQualityLabeledSpliceCreate(HighQualityLabeledSpliceBase):
    pass


class DeletedSpliceBase(_pydantic.BaseModel):
    name: str
    path: str
    label: str
    origin: str
    duration: str
    validation: str
    owner_id: str
    labeler_id: Optional[str] = None
    validator_id: Optional[str] = None


class DeletedSplice(DeletedSpliceBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class DeletedSpliceCreate(DeletedSpliceBase):
    pass


class SpliceBeingProcessedBase(_pydantic.BaseModel):
    name: str
    path: str
    label: str
    origin: str
    duration: str
    validation: str
    owner_id: str
    labeler_id: Optional[str] = None
    validator_id: Optional[str] = None

    status: str

class SpliceBeingProcessed(SpliceBeingProcessedBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class SpliceBeingProcessedCreate(SpliceBeingProcessedBase):
    pass



class BaseSpliceAction(_pydantic.BaseModel):
    id: int
    label: str
    validation: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None

class LabelSplice(BaseSpliceAction):
    pass

class ValidateSplice(BaseSpliceAction):
    validator_id: Optional[str] = None

class DeleteSplice(_pydantic.BaseModel):
    id: int


class UserBase(_pydantic.BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    accent: Optional[str] = None
    region: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    provider: Optional[str] = "local"

class User(UserBase):
    id: str
    created_at: _dt.datetime
    modified_at: _dt.datetime
    provider: str
    is_verified: bool = False
    profile_completed: bool = False
    model_config = _pydantic.ConfigDict(from_attributes=True)


# Profile completion schema (for Google users)
class CompleteProfileRequest(_pydantic.BaseModel):
    phone_number: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    accent: Optional[str] = None
    region: Optional[str] = None

class Token(_pydantic.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class TokenData(_pydantic.BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None


class RefreshTokenRequest(_pydantic.BaseModel):
    refresh_token: str


# Email verification schemas
class VerifyEmailRequest(_pydantic.BaseModel):
    email: str
    code: str

class ResendVerificationRequest(_pydantic.BaseModel):
    email: str

# Password reset schemas
class ForgotPasswordRequest(_pydantic.BaseModel):
    email: str

class ResetPasswordRequest(_pydantic.BaseModel):
    email: str
    code: str
    new_password: str

# Registration response
class RegisterResponse(_pydantic.BaseModel):
    message: str
    email: str
