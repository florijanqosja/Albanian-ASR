import datetime as _dt
import sqlalchemy as _sql
from sqlalchemy.orm import relationship

from . import database as _database
from .enums import MediaProcessingStatus


class User(_database.Base):
    __tablename__ = "users"
    id = _sql.Column(_sql.String, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    surname = _sql.Column(_sql.String, nullable=True)
    email = _sql.Column(_sql.String, unique=True, index=True, nullable=True)
    phone_number = _sql.Column(_sql.String, nullable=True)
    age = _sql.Column(_sql.Integer, nullable=True)
    nationality = _sql.Column(_sql.String, nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    modified_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow, onupdate=_dt.datetime.utcnow)
    accent = _sql.Column(_sql.String, nullable=True)
    region = _sql.Column(_sql.String, nullable=True)
    hashed_password = _sql.Column(_sql.String, nullable=True)
    provider = _sql.Column(_sql.String, default="local")
    avatar_url = _sql.Column(_sql.String, nullable=True)
    # Email verification fields
    is_verified = _sql.Column(_sql.Boolean, default=False)
    verification_code = _sql.Column(_sql.String, nullable=True)
    verification_code_expires = _sql.Column(_sql.DateTime, nullable=True)
    # Password reset fields
    reset_code = _sql.Column(_sql.String, nullable=True)
    reset_code_expires = _sql.Column(_sql.DateTime, nullable=True)
    # Profile completion (for Google users who need to provide additional info)
    profile_completed = _sql.Column(_sql.Boolean, default=False)


class Video(_database.Base):
    __tablename__ = "videos"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    category = _sql.Column(_sql.String, nullable=True)
    to_mp3_status = _sql.Column(_sql.String, nullable=True)
    splice_status = _sql.Column(_sql.String, nullable=True)
    mp3_path = _sql.Column(_sql.String, nullable=True)
    upload_time = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    uploader_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)
    processing_status = _sql.Column(
        _sql.Enum(MediaProcessingStatus, name="video_processing_status"),
        nullable=False,
        default=MediaProcessingStatus.IN_PROGRESS,
    )
    processing_error = _sql.Column(_sql.String, nullable=True)

class Splice(_database.Base):
    __tablename__ = "splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)


class LabeledSplice(_database.Base):
    __tablename__ = "labeled_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)


class HighQualityLabeledSplice(_database.Base):
    __tablename__ = "high_quality_labeled_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    validator_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True) # Original Labeler


class DeletedSplice(_database.Base):
    __tablename__ = "deleted_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)
    validator_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)


class SpliceBeingProcessed(_database.Base):
    __tablename__ = "splices_being_processed"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    status = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)
    validator_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)


class TextSplice(_database.Base):
    __tablename__ = "text_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    prompt_text = _sql.Column(_sql.String, unique=True, nullable=False)
    status = _sql.Column(_sql.String, nullable=False, default="pending")
    reserved_by = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)
    reserved_at = _sql.Column(_sql.DateTime, nullable=True)
    completed_at = _sql.Column(_sql.DateTime, nullable=True)
    recorded_splice_id = _sql.Column(_sql.Integer, _sql.ForeignKey("labeled_splices.id"), nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    updated_at = _sql.Column(
        _sql.DateTime,
        default=_dt.datetime.utcnow,
        onupdate=_dt.datetime.utcnow,
    )


class TextSpliceRecording(_database.Base):
    __tablename__ = "text_splice_recordings"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    text_splice_id = _sql.Column(_sql.Integer, _sql.ForeignKey("text_splices.id"), nullable=False)
    recorded_splice_id = _sql.Column(_sql.Integer, nullable=False)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=False)
    label = _sql.Column(_sql.String, nullable=False)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    updated_at = _sql.Column(
        _sql.DateTime,
        default=_dt.datetime.utcnow,
        onupdate=_dt.datetime.utcnow,
    )


class UploadRecord(_database.Base):
    __tablename__ = "upload_records"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.String, _sql.ForeignKey("users.id"), nullable=False)
    video_id = _sql.Column(_sql.Integer, _sql.ForeignKey("videos.id"), nullable=True)
    original_filename = _sql.Column(_sql.String, nullable=False)
    display_name = _sql.Column(_sql.String, nullable=False)
    category = _sql.Column(_sql.String, nullable=True)
    consent_version = _sql.Column(_sql.String, nullable=False, default="v1")
    consent_given = _sql.Column(_sql.Boolean, nullable=False, default=True)
    status = _sql.Column(
        _sql.Enum(MediaProcessingStatus, name="upload_status_enum"),
        nullable=False,
        default=MediaProcessingStatus.IN_PROGRESS,
    )
    error_message = _sql.Column(_sql.String, nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    updated_at = _sql.Column(
        _sql.DateTime,
        default=_dt.datetime.utcnow,
        onupdate=_dt.datetime.utcnow,
    )

