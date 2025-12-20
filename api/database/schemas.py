import datetime as _dt
from typing import Optional, Generic, TypeVar
from uuid import UUID
import pydantic as _pydantic

from .enums import MediaProcessingStatus

T = TypeVar('T')

class ResponseModel(_pydantic.BaseModel, Generic[T]):
    status: str
    data: Optional[T] = None
    message: Optional[str] = None


class PolicyConsentBase(_pydantic.BaseModel):
    version: str
    effective_date: _dt.date
    privacy_content: str
    terms_content: str


class PolicyConsent(PolicyConsentBase):
    id: UUID
    created_at: _dt.datetime
    updated_at: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)


class PolicyConsentCreate(PolicyConsentBase):
    pass


class VideoBase(_pydantic.BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    category: Optional[str] = None
    to_mp3_status: Optional[str] = None
    splice_status: Optional[str] = None
    mp3_path: Optional[str] = None
    uploader_id: Optional[UUID] = None
    processing_status: Optional[MediaProcessingStatus] = MediaProcessingStatus.IN_PROGRESS
    processing_error: Optional[str] = None

class Video(VideoBase):
    id: UUID
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
    owner_id: UUID


class Splice(SpliceBase):
    id: UUID
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
    owner_id: UUID
    labeler_id: Optional[UUID] = None


class LabeledSplice(LabeledSpliceBase):
    id: UUID
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
    owner_id: UUID
    validator_id: UUID
    labeler_id: Optional[UUID] = None


class UploadStats(_pydantic.BaseModel):
    total_generated: int = 0
    validated_count: int = 0
    labeled_count: int = 0
    unlabeled_count: int = 0


class HighQualityLabeledSplice(HighQualityLabeledSpliceBase):
    id: UUID
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
    owner_id: UUID
    labeler_id: Optional[UUID] = None
    validator_id: Optional[UUID] = None


class DeletedSplice(DeletedSpliceBase):
    id: UUID
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
    owner_id: UUID
    labeler_id: Optional[UUID] = None
    validator_id: Optional[UUID] = None

    status: str

class SpliceBeingProcessed(SpliceBeingProcessedBase):
    id: UUID
    model_config = _pydantic.ConfigDict(from_attributes=True)

class SpliceBeingProcessedCreate(SpliceBeingProcessedBase):
    pass


class TextSpliceBase(_pydantic.BaseModel):
    prompt_text: str
    status: str = "pending"
    reserved_by: Optional[UUID] = None
    reserved_at: Optional[_dt.datetime] = None
    completed_at: Optional[_dt.datetime] = None
    recorded_splice_id: Optional[UUID] = None


class TextSplice(TextSpliceBase):
    id: UUID
    created_at: _dt.datetime
    updated_at: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)


class TextSpliceCreate(_pydantic.BaseModel):
    prompt_text: str


class TextSpliceUpdate(_pydantic.BaseModel):
    status: Optional[str] = None
    reserved_by: Optional[UUID] = None
    reserved_at: Optional[_dt.datetime] = None
    completed_at: Optional[_dt.datetime] = None
    recorded_splice_id: Optional[UUID] = None


class TextSpliceRecordingBase(_pydantic.BaseModel):
    text_splice_id: UUID
    recorded_splice_id: UUID
    name: Optional[str] = None
    path: str
    label: str
    origin: Optional[str] = None
    duration: Optional[str] = None
    validation: Optional[str] = None
    owner_id: UUID
    labeler_id: Optional[UUID] = None


class TextSpliceRecording(TextSpliceRecordingBase):
    id: UUID
    created_at: _dt.datetime
    updated_at: _dt.datetime
    model_config = _pydantic.ConfigDict(from_attributes=True)


class TextSpliceRecordingCreate(TextSpliceRecordingBase):
    pass


class UploadRecordBase(_pydantic.BaseModel):
    user_id: UUID
    video_id: Optional[UUID] = None
    original_filename: str
    display_name: str
    category: Optional[str] = None
    consent_version: str = "v1"
    consent_given: bool = True
    status: MediaProcessingStatus = MediaProcessingStatus.IN_PROGRESS
    error_message: Optional[str] = None


class UploadRecord(UploadRecordBase):
    id: UUID
    created_at: _dt.datetime
    updated_at: _dt.datetime
    stats: UploadStats = UploadStats()
    model_config = _pydantic.ConfigDict(from_attributes=True)


class UploadRecordCreate(UploadRecordBase):
    pass

class SupportMessageRequest(_pydantic.BaseModel):
    name: str
    surname: str
    email: str
    message: str

    @_pydantic.field_validator("name", "surname")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        """
        Validate and normalize a name or surname by trimming surrounding whitespace and enforcing length limits.
        
        Parameters:
            value (str): The raw name string to validate.
        
        Returns:
            str: The trimmed name.
        
        Raises:
            ValueError: "Required" if the trimmed value is empty; "Too long" if the trimmed value has more than 100 characters.
        """
        value = value.strip()
        if not value:
            raise ValueError("Required")
        if len(value) > 100:
            raise ValueError("Too long")
        return value

    @_pydantic.field_validator("message")
    @classmethod
    def _strip_message(cls, value: str) -> str:
        """
        Validate and trim a support message string.
        
        Trims surrounding whitespace and ensures the message is not empty and does not exceed 5000 characters.
        
        Parameters:
            value (str): The input message string to validate and trim.
        
        Returns:
            str: The trimmed message.
        
        Raises:
            ValueError: If the trimmed message is empty ("Required") or longer than 5000 characters ("Too long").
        """
        value = value.strip()
        if not value:
            raise ValueError("Required")
        if len(value) > 5000:
            raise ValueError("Too long")
        return value

    @_pydantic.field_validator("email")
    @classmethod
    def _strip_email(cls, value: str) -> str:
        """
        Validate and normalize an email address.
        
        Strips surrounding whitespace and enforces that the email is present, does not exceed 320 characters, and contains a single '@' that is not at the start or end.
        
        Parameters:
            value (str): The email address to validate.
        
        Returns:
            str: The trimmed, validated email address.
        
        Raises:
            ValueError: With message "Required" if empty after trimming, "Too long" if length > 320, or "Invalid email" if the '@' character is missing or placed at the start or end.
        """
        value = value.strip()
        if not value:
            raise ValueError("Required")
        if len(value) > 320:
            raise ValueError("Too long")
        if "@" not in value or value.startswith("@") or value.endswith("@"):  # lightweight check
            raise ValueError("Invalid email")
        return value


class ActivityItem(_pydantic.BaseModel):
    id: UUID
    name: Optional[str] = None
    path: Optional[str] = None
    label: Optional[str] = None
    origin: Optional[str] = None
    duration: Optional[str] = None
    validation: Optional[str] = None
    owner_id: Optional[UUID] = None
    labeler_id: Optional[UUID] = None
    validator_id: Optional[UUID] = None
    activity_type: str
    stats: UploadStats = UploadStats()
    model_config = _pydantic.ConfigDict(from_attributes=True)



class BaseSpliceAction(_pydantic.BaseModel):
    id: UUID
    label: str
    validation: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None

class LabelSplice(BaseSpliceAction):
    pass

class ValidateSplice(BaseSpliceAction):
    validator_id: Optional[UUID] = None

class DeleteSplice(_pydantic.BaseModel):
    id: UUID


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
    consent_id: UUID

class User(UserBase):
    id: UUID
    created_at: _dt.datetime
    modified_at: _dt.datetime
    provider: str
    is_verified: bool = False
    profile_completed: bool = False
    consent_id: UUID
    model_config = _pydantic.ConfigDict(from_attributes=True)


class DeleteAccountRequest(_pydantic.BaseModel):
    acknowledge_data_retention: bool
    acknowledge_future_request: bool

    @_pydantic.field_validator("acknowledge_data_retention", "acknowledge_future_request")
    @classmethod
    def _must_acknowledge(cls, value: bool) -> bool:
        """
        Validate that a boolean acknowledgment is explicitly True.
        
        Parameters:
            value (bool): The value to validate.
        
        Returns:
            bool: `True` if the provided value is True.
        
        Raises:
            ValueError: If `value` is not True with the message "Please confirm to continue".
        """
        if value is not True:
            raise ValueError("Please confirm to continue")
        return value


class DeleteAccountResult(_pydantic.BaseModel):
    user_id: UUID
    anonymized: bool = True


# Profile completion schema (for Google users)
class CompleteProfileRequest(_pydantic.BaseModel):
    phone_number: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    accent: Optional[str] = None
    region: Optional[str] = None
    consent_id: UUID

class Token(_pydantic.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class TokenData(_pydantic.BaseModel):
    email: Optional[str] = None
    user_id: Optional[UUID] = None


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