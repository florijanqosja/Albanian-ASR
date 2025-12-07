import datetime as _dt
from typing import Optional, Generic, TypeVar, Any
import pydantic as _pydantic

from .enums import MediaProcessingStatus

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
    uploader_id: Optional[str] = None
    processing_status: Optional[MediaProcessingStatus] = MediaProcessingStatus.IN_PROGRESS
    processing_error: Optional[str] = None

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


class UploadStats(_pydantic.BaseModel):
    total_generated: int = 0
    validated_count: int = 0
    labeled_count: int = 0
    unlabeled_count: int = 0


class HighQualityLabeledSplice(HighQualityLabeledSpliceBase):
    id: int
    stats: UploadStats = UploadStats()
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


class TextSpliceBase(_pydantic.BaseModel):
    prompt_text: str
    status: str = "pending"
    reserved_by: Optional[str] = None
    reserved_at: Optional[_dt.datetime] = None
    completed_at: Optional[_dt.datetime] = None
    recorded_splice_id: Optional[int] = None


class TextSplice(TextSpliceBase):
    id: int
    created_at: _dt.datetime
    updated_at: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)


class TextSpliceCreate(_pydantic.BaseModel):
    prompt_text: str


class TextSpliceUpdate(_pydantic.BaseModel):
    status: Optional[str] = None
    reserved_by: Optional[str] = None
    reserved_at: Optional[_dt.datetime] = None
    completed_at: Optional[_dt.datetime] = None
    recorded_splice_id: Optional[int] = None


class TextSpliceRecordingBase(_pydantic.BaseModel):
    text_splice_id: int
    recorded_splice_id: int
    name: Optional[str] = None
    path: str
    label: str
    origin: Optional[str] = None
    duration: Optional[str] = None
    validation: Optional[str] = None
    owner_id: str
    labeler_id: Optional[str] = None


class TextSpliceRecording(TextSpliceRecordingBase):
    id: int
    created_at: _dt.datetime
    updated_at: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)


class TextSpliceRecordingCreate(TextSpliceRecordingBase):
    pass


class UploadRecordBase(_pydantic.BaseModel):
    user_id: str
    video_id: Optional[int] = None
    original_filename: str
    display_name: str
    category: Optional[str] = None
    consent_version: str = "v1"
    consent_given: bool = True
    status: MediaProcessingStatus = MediaProcessingStatus.IN_PROGRESS
    error_message: Optional[str] = None


class UploadRecord(UploadRecordBase):
    id: int
    created_at: _dt.datetime
    updated_at: _dt.datetime
    stats: UploadStats = UploadStats()
    model_config = _pydantic.ConfigDict(from_attributes=True)


class UploadRecordCreate(UploadRecordBase):
    pass


class ActivityItem(_pydantic.BaseModel):
    id: int
    name: Optional[str] = None
    path: Optional[str] = None
    label: Optional[str] = None
    origin: Optional[str] = None
    duration: Optional[str] = None
    validation: Optional[str] = None
    owner_id: Optional[str] = None
    labeler_id: Optional[str] = None
    validator_id: Optional[str] = None
    activity_type: str
    stats: UploadStats = UploadStats()
    model_config = _pydantic.ConfigDict(from_attributes=True)



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
