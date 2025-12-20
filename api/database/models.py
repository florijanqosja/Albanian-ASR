import sqlalchemy as _sql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import database as _database
from .enums import MediaProcessingStatus


def _uuid_pk() -> _sql.Column:
    """
    Return a SQLAlchemy Column configured as a UUID primary key.
    
    The column is configured to use Python UUID objects, is indexed, and has a Postgres server default of `gen_random_uuid()`.
    
    Returns:
        sqlalchemy.Column: A UUID primary key column with an index and `gen_random_uuid()` as the server default.
    """
    return _sql.Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        server_default=_sql.text("gen_random_uuid()"),
    )


def _created_at_column() -> _sql.Column:
    """
    Create a SQLAlchemy Column for timezone-aware creation timestamps.
    
    Returns:
        _sql.Column: A non-nullable timezone-aware `DateTime` column with a server default of `now()`.
    """
    return _sql.Column(
        _sql.DateTime(timezone=True),
        nullable=False,
        server_default=_sql.func.now(),
    )


def _updated_at_column() -> _sql.Column:
    """
    Create a SQLAlchemy Column for a timezone-aware `DateTime` that tracks last-update timestamps.
    
    The column is non-nullable, has a server default of `now()` and automatically updates to `now()` on row updates.
    
    Returns:
        _sql.Column: A configured `DateTime` column with timezone support, `server_default=_sql.func.now()`, and `onupdate=_sql.func.now()`.
    """
    return _sql.Column(
        _sql.DateTime(timezone=True),
        nullable=False,
        server_default=_sql.func.now(),
        onupdate=_sql.func.now(),
    )


class PolicyConsent(_database.Base):
    __tablename__ = "policy_consents"

    id = _uuid_pk()
    version = _sql.Column(_sql.String, nullable=False, unique=True)
    effective_date = _sql.Column(_sql.Date, nullable=False)
    privacy_content = _sql.Column(_sql.Text, nullable=False)
    terms_content = _sql.Column(_sql.Text, nullable=False)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class User(_database.Base):
    __tablename__ = "users"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    surname = _sql.Column(_sql.String, nullable=True)
    email = _sql.Column(_sql.String, unique=True, index=True, nullable=True)
    phone_number = _sql.Column(_sql.String, nullable=True)
    age = _sql.Column(_sql.Integer, nullable=True)
    nationality = _sql.Column(_sql.String, nullable=True)
    created_at = _created_at_column()
    modified_at = _updated_at_column()
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
    token_version = _sql.Column(_sql.Integer, nullable=False, default=0)
    consent_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("policy_consents.id"), nullable=False)
    consent = relationship(PolicyConsent)


class Video(_database.Base):
    __tablename__ = "videos"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    category = _sql.Column(_sql.String, nullable=True)
    to_mp3_status = _sql.Column(_sql.String, nullable=True)
    splice_status = _sql.Column(_sql.String, nullable=True)
    mp3_path = _sql.Column(_sql.String, nullable=True)
    upload_time = _sql.Column(
        _sql.DateTime(timezone=True),
        nullable=False,
        server_default=_sql.func.now(),
    )
    uploader_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    processing_status = _sql.Column(
        _sql.Enum(MediaProcessingStatus, name="video_processing_status"),
        nullable=False,
        default=MediaProcessingStatus.IN_PROGRESS,
    )
    processing_error = _sql.Column(_sql.String, nullable=True)
    updated_at = _updated_at_column()

class Splice(_database.Base):
    __tablename__ = "splices"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class LabeledSplice(_database.Base):
    __tablename__ = "labeled_splices"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class HighQualityLabeledSplice(_database.Base):
    __tablename__ = "high_quality_labeled_splices"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    validator_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True) # Original Labeler
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class DeletedSplice(_database.Base):
    __tablename__ = "deleted_splices"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    validator_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class SpliceBeingProcessed(_database.Base):
    __tablename__ = "splices_being_processed"
    id = _uuid_pk()
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    status = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    validator_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class TextSplice(_database.Base):
    __tablename__ = "text_splices"
    id = _uuid_pk()
    prompt_text = _sql.Column(_sql.String, unique=True, nullable=False)
    status = _sql.Column(_sql.String, nullable=False, default="pending")
    reserved_by = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    reserved_at = _sql.Column(_sql.DateTime(timezone=True), nullable=True)
    completed_at = _sql.Column(_sql.DateTime(timezone=True), nullable=True)
    recorded_splice_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("labeled_splices.id"), nullable=True)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class TextSpliceRecording(_database.Base):
    __tablename__ = "text_splice_recordings"
    id = _uuid_pk()
    text_splice_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("text_splices.id"), nullable=False)
    recorded_splice_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("labeled_splices.id"), nullable=False)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=False)
    label = _sql.Column(_sql.String, nullable=False)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)
    owner_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    labeler_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=True)
    created_at = _created_at_column()
    updated_at = _updated_at_column()


class UploadRecord(_database.Base):
    __tablename__ = "upload_records"

    id = _uuid_pk()
    user_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("users.id"), nullable=False)
    video_id = _sql.Column(UUID(as_uuid=True), _sql.ForeignKey("videos.id"), nullable=True)
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
    created_at = _created_at_column()
    updated_at = _updated_at_column()
