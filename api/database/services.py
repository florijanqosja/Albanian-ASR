import datetime as _dt
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, literal, select, union_all
import sqlalchemy as _sql

from . import database as _database
from . import models as _models
from . import schemas as _schemas
from .enums import MediaProcessingStatus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _add_tables():
    """
    Ensure the PostgreSQL pgcrypto extension exists and create all database tables from the module metadata.
    
    This initializes database schema by creating the "pgcrypto" extension if it is missing, then invoking the SQLAlchemy metadata to create all configured tables.
    """
    with _database.engine.begin() as conn:
        conn.execute(_sql.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
    return _database.Base.metadata.create_all(bind=_database.engine)

SessionLocal = _database.SessionLocal

def get_db():
    """
    Yield a database session and ensure it is closed after use.
    
    Returns:
        db (Session): An open SQLAlchemy session that will be closed when the generator exits.
    """
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_policy_consent(db: "Session", consent: _schemas.PolicyConsentCreate) -> _schemas.PolicyConsent:
    """
    Create a new PolicyConsent database record from the provided create schema and return the validated PolicyConsent schema.
    
    Parameters:
        consent (_schemas.PolicyConsentCreate): Data used to create the new policy consent, including version, effective_date, privacy_content, and terms_content.
    
    Returns:
        _schemas.PolicyConsent: The created PolicyConsent validated and returned as a schema.
    """
    record = _models.PolicyConsent(**consent.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _schemas.PolicyConsent.model_validate(record)


def get_policy_consent_by_id(db: "Session", consent_id: UUID) -> Optional[_models.PolicyConsent]:
    """
    Retrieve the PolicyConsent record for the given consent identifier.
    
    Parameters:
        consent_id (UUID): UUID of the PolicyConsent to fetch.
    
    Returns:
        _models.PolicyConsent | None: The matching PolicyConsent model if found, `None` otherwise.
    """
    return db.query(_models.PolicyConsent).filter(_models.PolicyConsent.id == consent_id).first()


def get_latest_policy_consent_model(db: "Session") -> Optional[_models.PolicyConsent]:
    """
    Retrieve the most recently effective PolicyConsent record.
    
    Searches PolicyConsent entries ordered by effective_date (newest first) and created_at (newest first) and returns the first match.
    
    Returns:
        _models.PolicyConsent | None: The most recent PolicyConsent model instance, or `None` if no records exist.
    """
    return (
        db.query(_models.PolicyConsent)
        .order_by(_models.PolicyConsent.effective_date.desc(), _models.PolicyConsent.created_at.desc())
        .first()
    )


def get_latest_policy_consent(db: "Session") -> Optional[_schemas.PolicyConsent]:
    """
    Retrieve the most recently effective PolicyConsent record.
    
    Returns:
        _schemas.PolicyConsent | None: A PolicyConsent schema for the most recently effective record, or `None` if no consent exists.
    """
    record = get_latest_policy_consent_model(db)
    return _schemas.PolicyConsent.model_validate(record) if record else None


def ensure_policy_consent(
    db: "Session",
    *,
    version: str,
    effective_date: _dt.date,
    privacy_content: str,
    terms_content: str,
) -> _models.PolicyConsent:
    """
    Ensure a PolicyConsent record with the given version exists, creating and persisting a new record if none is found.
    
    Parameters:
        version (str): The policy version identifier to ensure.
        effective_date (datetime.date): The date when this policy version becomes effective.
        privacy_content (str): The privacy policy text for this version.
        terms_content (str): The terms of service text for this version.
    
    Returns:
        _models.PolicyConsent: The existing or newly created PolicyConsent ORM instance corresponding to `version`.
    """
    existing = db.query(_models.PolicyConsent).filter(_models.PolicyConsent.version == version).first()
    if existing:
        return existing

    record = _models.PolicyConsent(
        version=version,
        effective_date=effective_date,
        privacy_content=privacy_content,
        terms_content=terms_content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

async def create_video(video: _schemas.VideoCreate, db: "Session") -> _schemas.Video:
    """
    Create a Video record from the provided VideoCreate schema and persist it to the database.
    
    Parameters:
        video (_schemas.VideoCreate): Data used to create the Video record.
    
    Returns:
        _schemas.Video: The created Video validated and returned as a schema.
    """
    video_db = _models.Video(**video.model_dump())
    db.add(video_db)
    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)

async def update_video(video_path: str, update_data: dict, db: "Session") -> _schemas.Video:
    """
    Update a Video record identified by its path with the provided fields.
    
    Parameters:
        video_path (str): Path identifying the Video to update.
        update_data (dict): Mapping of Video attribute names to their new values.
    
    Returns:
        _schemas.Video: The updated Video as a validated schema.
    
    Raises:
        HTTPException: 404 if no Video with the given path exists.
    """
    video_db = db.query(_models.Video).filter(_models.Video.path == video_path).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)


async def update_video_by_id(video_id: UUID, update_data: dict, db: "Session") -> _schemas.Video:
    """
    Update fields on an existing Video identified by its UUID.
    
    Parameters:
        video_id (UUID): UUID of the Video to update.
        update_data (dict): Mapping of Video attribute names to new values to apply.
    
    Returns:
        _schemas.Video: The updated Video validated as a schema.
    
    Raises:
        HTTPException: 404 if no Video with the given `video_id` exists.
    """
    video_db = db.query(_models.Video).filter(_models.Video.id == video_id).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)

async def update_splice_being_processed(splice_id: UUID, data: dict, db: "Session") -> _schemas.SpliceBeingProcessed:
    """
    Update fields on a SpliceBeingProcessed identified by its UUID and return the updated record.
    
    Parameters:
        splice_id (UUID): UUID of the SpliceBeingProcessed to update.
        data (dict): Mapping of model attribute names to their new values; keys must match writable model attributes.
        db (Session): Database session (omitted from detailed docs for common service parameters).
    
    Returns:
        _schemas.SpliceBeingProcessed: The updated SpliceBeingProcessed validated as a schema.
    
    Raises:
        HTTPException: 404 if no SpliceBeingProcessed with the given `splice_id` exists.
    """
    splice_being_processed_db = db.query(_models.SpliceBeingProcessed).filter(_models.SpliceBeingProcessed.id == splice_id).first()
    if splice_being_processed_db is None:
        raise HTTPException(404, detail="Splice not found")

    for key, value in data.items():
        setattr(splice_being_processed_db, key, value)

    db.commit()
    db.refresh(splice_being_processed_db)
    return _schemas.SpliceBeingProcessed.model_validate(splice_being_processed_db)

async def create_splice(splice: _schemas.SpliceCreate, db: "Session") -> _schemas.Splice:
    splice_db = _models.Splice(**splice.model_dump())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.Splice.model_validate(splice_db)

async def persist_processing_success(
    db: "Session",
    *,
    video_id: UUID,
    video_update: dict,
    splices: "list[_schemas.SpliceCreate]",
    upload_record_id: Optional[UUID] = None,
) -> int:
    """
    Persist a video's splices AND its terminal statuses in ONE transaction.

    Everything commits together so a mid-flight failure can never leave committed orphan
    splices under a video that ends up marked ERROR (which would still name-join into
    upload-history stats), nor flip an already-COMPLETED video back to ERROR because a
    follow-up bookkeeping commit failed. Either all of it lands or none of it does.

    Replaces the old per-splice commits (one connection checkout + commit per segment, up
    to ~190 per video) that exhausted the SQLAlchemy pool under concurrent uploads. The
    splices go in via a single multi-row INSERT (one round-trip) rather than one statement
    per row; omitted columns (id/created_at/updated_at) fall back to their server defaults.

    Returns:
        int: Number of splice rows inserted.

    Raises:
        HTTPException: 404 if no Video with `video_id` exists.
    """
    video_db = db.query(_models.Video).filter(_models.Video.id == video_id).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    if splices:
        db.execute(
            _sql.insert(_models.Splice).values([splice.model_dump() for splice in splices])
        )

    for key, value in video_update.items():
        setattr(video_db, key, value)

    if upload_record_id is not None:
        upload_db = (
            db.query(_models.UploadRecord)
            .filter(_models.UploadRecord.id == upload_record_id)
            .first()
        )
        if upload_db is not None:
            upload_db.status = MediaProcessingStatus.COMPLETED
            upload_db.error_message = None

    db.commit()
    return len(splices)


async def persist_processing_error(
    db: "Session",
    *,
    video_id: UUID,
    error: str,
    upload_record_id: Optional[UUID] = None,
) -> None:
    """
    Mark a video (and its upload record, if any) ERROR in ONE transaction, best-effort.

    Used on the failure path. Missing rows are tolerated rather than raising so the error
    handler never masks the original processing exception with a secondary one.
    """
    video_db = db.query(_models.Video).filter(_models.Video.id == video_id).first()
    if video_db is not None:
        video_db.processing_status = MediaProcessingStatus.ERROR
        video_db.processing_error = error

    if upload_record_id is not None:
        upload_db = (
            db.query(_models.UploadRecord)
            .filter(_models.UploadRecord.id == upload_record_id)
            .first()
        )
        if upload_db is not None:
            upload_db.status = MediaProcessingStatus.ERROR
            upload_db.error_message = error

    db.commit()

async def create_splice_being_processed(splice: _schemas.SpliceBeingProcessedCreate, db: "Session") -> _schemas.SpliceBeingProcessed:
    splice_dict = splice.model_dump()
    splice_being_processed_db = _models.SpliceBeingProcessed(**splice_dict)
    db.add(splice_being_processed_db)
    db.commit()
    db.refresh(splice_being_processed_db)
    return _schemas.SpliceBeingProcessed.model_validate(splice_being_processed_db)


async def create_upload_record(upload: _schemas.UploadRecordCreate, db: "Session") -> _schemas.UploadRecord:
    """
    Create a new upload record in the database from the provided create schema.
    
    Parameters:
        upload (_schemas.UploadRecordCreate): Data used to populate the new upload record.
    
    Returns:
        _schemas.UploadRecord: The created upload record validated and returned as a schema.
    """
    upload_db = _models.UploadRecord(**upload.model_dump())
    db.add(upload_db)
    db.commit()
    db.refresh(upload_db)
    return _schemas.UploadRecord.model_validate(upload_db)


def update_upload_record(upload_id: UUID, data: dict, db: "Session") -> _schemas.UploadRecord:
    """
    Update fields on an existing upload record identified by its UUID.
    
    Parameters:
        upload_id (UUID): UUID of the upload record to update.
        data (dict): Mapping of model field names to new values to apply.
    
    Returns:
        _schemas.UploadRecord: The updated upload record as a validated schema.
    
    Raises:
        HTTPException: 404 if no upload record with the given `upload_id` exists.
    """
    record = db.query(_models.UploadRecord).filter(_models.UploadRecord.id == upload_id).first()
    if record is None:
        raise HTTPException(404, detail="Upload record not found")

    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return _schemas.UploadRecord.model_validate(record)


def set_upload_status(
    upload_id: UUID,
    status: MediaProcessingStatus,
    db: "Session",
    error_message: Optional[str] = None,
) -> _schemas.UploadRecord:
    """
    Set the processing status for an upload record.
    
    If provided, associates `error_message` with the upload (commonly used when setting an error status).
    
    Parameters:
        upload_id (UUID): Identifier of the upload record to update.
        status (MediaProcessingStatus): New processing status to assign.
        error_message (Optional[str]): Optional error message to store with the upload when applicable.
    
    Returns:
        _schemas.UploadRecord: The updated upload record.
    """
    payload = {"status": status}
    if error_message is not None:
        payload["error_message"] = error_message
    return update_upload_record(upload_id, payload, db)

async def delete_labeled_splice(splice_id: UUID, db: "Session"):
    """
    Delete a labeled splice and preserve any referencing text splice recordings.
    
    Removes the LabeledSplice with the given `splice_id`. For each TextSplice that referenced the deleted splice, a TextSpliceRecording snapshot is created if one does not already exist, and the TextSplice's recorded_splice_id is cleared and marked as updated.
    
    Parameters:
        splice_id (UUID): Identifier of the LabeledSplice to delete.
    
    """
    labeled_splice = (
        db.query(_models.LabeledSplice)
        .filter(_models.LabeledSplice.id == splice_id)
        .first()
    )
    if not labeled_splice:
        return

    referencing_text_splices = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.recorded_splice_id == splice_id)
        .all()
    )

    for text_splice in referencing_text_splices:
        existing_snapshot = (
            db.query(_models.TextSpliceRecording)
            .filter(_models.TextSpliceRecording.text_splice_id == text_splice.id)
            .first()
        )
        if not existing_snapshot:
            snapshot_db = _models.TextSpliceRecording(
                text_splice_id=text_splice.id,
                recorded_splice_id=splice_id,
                name=labeled_splice.name,
                path=labeled_splice.path,
                label=labeled_splice.label or "",
                origin=labeled_splice.origin,
                duration=labeled_splice.duration,
                validation=labeled_splice.validation,
                owner_id=labeled_splice.owner_id,
                labeler_id=labeled_splice.labeler_id or text_splice.reserved_by,
            )
            db.add(snapshot_db)
        text_splice.recorded_splice_id = None
        text_splice.updated_at = _dt.datetime.utcnow()

    db.delete(labeled_splice)
    db.commit()

async def delete_splice(splice_id: UUID, db: "Session"):
    """
    Delete the Splice record with the given UUID from the database.
    
    Deletes the Splice identified by splice_id if it exists; the operation is idempotent and commits the transaction.
    """
    db.query(_models.Splice).filter(_models.Splice.id == splice_id).delete()
    db.commit()

async def get_first_labeled_splice(db: "Session") -> _schemas.LabeledSplice:
    """
    Retrieve the earliest created labeled splice.
    
    Returns:
        _schemas.LabeledSplice | None: The validated `LabeledSplice` schema for the earliest created record, or `None` if no labeled splices exist.
    """
    first_splice = db.query(_models.LabeledSplice).order_by(_models.LabeledSplice.created_at).first()
    return _schemas.LabeledSplice.model_validate(first_splice) if first_splice else None

async def get_first_splice(db: "Session") -> _schemas.Splice:
    """
    Retrieve the earliest-created Splice from the database.
    
    Returns:
        _schemas.Splice: The earliest-created splice as a validated schema, or `None` if no splice exists.
    """
    first_splice = db.query(_models.Splice).order_by(_models.Splice.created_at).first()
    return _schemas.Splice.model_validate(first_splice) if first_splice else None

async def get_splice_being_processed(splice_id: UUID, db: "Session") -> _schemas.SpliceBeingProcessed:
    """
    Retrieve a SpliceBeingProcessed record by its UUID.
    
    Returns:
        The SpliceBeingProcessed model instance if found, otherwise None.
    """
    return db.query(_models.SpliceBeingProcessed).get(splice_id)

async def delete_splice_being_processed(splice: _schemas.SpliceBeingProcessed, db: "Session") -> None:
    """
    Delete a SpliceBeingProcessed record from the database.
    
    Parameters:
        splice (_schemas.SpliceBeingProcessed): The SpliceBeingProcessed instance to remove.
    
    Raises:
        HTTPException: with status code 500 and the underlying error message if deletion or commit fails.
    """
    try:
        db.delete(splice)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_text_splice(text_splice: _schemas.TextSpliceCreate, db: "Session") -> _schemas.TextSplice:
    """
    Create a TextSplice record from the provided prompt and mark it as pending.
    
    Strips surrounding whitespace from `text_splice.prompt_text`, validates it is not empty, persists a new TextSplice with status "pending", and returns the validated TextSplice schema.
    
    Parameters:
        text_splice (_schemas.TextSpliceCreate): Input data; `prompt_text` is required and will be trimmed.
        db (Session): Database session used to persist the record.
    
    Returns:
        _schemas.TextSplice: The created TextSplice validated as a schema.
    
    Raises:
        HTTPException: 400 if `prompt_text` is empty after trimming.
    """
    prompt_text = text_splice.prompt_text.strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt text cannot be empty")

    text_splice_db = _models.TextSplice(prompt_text=prompt_text, status="pending")
    db.add(text_splice_db)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(text_splice_db)
    return _schemas.TextSplice.model_validate(text_splice_db)


async def update_text_splice(text_splice_id: UUID, update_data: dict, db: "Session") -> _schemas.TextSplice:
    """
    Update fields on an existing TextSplice record.
    
    Parameters:
        text_splice_id (UUID): Identifier of the TextSplice to update.
        update_data (dict): Mapping of model attribute names to new values to apply.
        db (Session): Database session used to perform the update.
    
    Returns:
        _schemas.TextSplice: The updated TextSplice validated as a schema.
    
    Raises:
        HTTPException: 404 if no TextSplice with the given id exists.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.id == text_splice_id)
        .first()
    )
    if text_splice_db is None:
        raise HTTPException(status_code=404, detail="Text splice not found")

    for key, value in update_data.items():
        setattr(text_splice_db, key, value)

    db.commit()
    db.refresh(text_splice_db)
    return _schemas.TextSplice.model_validate(text_splice_db)


async def reserve_text_splice(text_splice_id: UUID, user_id: UUID, db: "Session") -> _schemas.TextSplice:
    """
    Reserve a pending text splice for a specific user.
    
    Parameters:
        text_splice_id (UUID): Identifier of the text splice to reserve.
        user_id (UUID): Identifier of the user reserving the text splice.
    
    Returns:
        TextSplice: The reserved text splice as a validated schema.
    
    Raises:
        HTTPException: 404 if the text splice does not exist.
        HTTPException: 409 if the text splice is not available to be reserved.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.id == text_splice_id)
        .first()
    )
    if text_splice_db is None:
        raise HTTPException(status_code=404, detail="Text splice not found")

    if text_splice_db.status not in {"pending", "reserved"} or (
        text_splice_db.status == "reserved" and text_splice_db.reserved_by != user_id
    ):
        raise HTTPException(status_code=409, detail="Text splice is not available")

    text_splice_db.status = "reserved"
    text_splice_db.reserved_by = user_id
    text_splice_db.reserved_at = _dt.datetime.utcnow()
    db.commit()
    db.refresh(text_splice_db)
    return _schemas.TextSplice.model_validate(text_splice_db)


def get_text_splice_by_id(db: "Session", text_splice_id: UUID) -> Optional[_schemas.TextSplice]:
    """
    Retrieve a TextSplice by its UUID.
    
    Returns:
        A TextSplice schema when a record with the given id exists, `None` otherwise.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.id == text_splice_id)
        .first()
    )
    return _schemas.TextSplice.model_validate(text_splice_db) if text_splice_db else None


def get_reserved_text_splice_for_user(db: "Session", user_id: UUID) -> Optional[_schemas.TextSplice]:
    """
    Fetches the most recently reserved TextSplice for a given user.
    
    Returns:
        _schemas.TextSplice: The most recently reserved TextSplice for the user, or `None` if no reserved splice exists.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(
            _models.TextSplice.status == "reserved",
            _models.TextSplice.reserved_by == user_id,
        )
        .order_by(_models.TextSplice.reserved_at.desc())
        .first()
    )
    return _schemas.TextSplice.model_validate(text_splice_db) if text_splice_db else None


async def complete_text_splice(
    text_splice_id: UUID,
    recorded_splice_id: Optional[UUID],
    db: "Session",
) -> _schemas.TextSplice:
    """
    Mark a text splice as completed and optionally associate it with a recorded splice.
    
    Parameters:
    	text_splice_id (UUID): Identifier of the TextSplice to mark completed.
    	recorded_splice_id (Optional[UUID]): Identifier of the associated recorded splice, or `None` to leave unlinked.
    
    Returns:
    	_text_splice (TextSplice): The updated TextSplice schema reflecting completion.
    
    Raises:
    	HTTPException: 404 if the specified TextSplice does not exist.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.id == text_splice_id)
        .first()
    )
    if text_splice_db is None:
        raise HTTPException(status_code=404, detail="Text splice not found")

    text_splice_db.status = "completed"
    text_splice_db.completed_at = _dt.datetime.utcnow()
    text_splice_db.recorded_splice_id = recorded_splice_id
    db.commit()
    db.refresh(text_splice_db)
    return _schemas.TextSplice.model_validate(text_splice_db)


def get_next_available_text_splice(db: "Session") -> Optional[_schemas.TextSplice]:
    """
    Fetches the oldest TextSplice record with status "pending".
    
    Returns:
        _schemas.TextSplice: The oldest pending TextSplice as a validated schema, or `None` if no pending record exists.
    """
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.status == "pending")
        .order_by(_models.TextSplice.created_at)
        .first()
    )
    return (
        _schemas.TextSplice.model_validate(text_splice_db)
        if text_splice_db
        else None
    )


async def create_text_splice_recording(
    recording: _schemas.TextSpliceRecordingCreate,
    db: "Session",
) -> _schemas.TextSpliceRecording:
    recording_db = _models.TextSpliceRecording(**recording.model_dump())
    db.add(recording_db)
    db.commit()
    db.refresh(recording_db)
    return _schemas.TextSpliceRecording.model_validate(recording_db)


def get_text_splice_recording_by_text_id(
    db: "Session", text_splice_id: UUID
) -> Optional[_schemas.TextSpliceRecording]:
    """
    Retrieve the recording associated with a specific text splice.
    
    Parameters:
        text_splice_id (UUID): The UUID of the TextSplice whose recording to retrieve.
    
    Returns:
        TextSpliceRecording | None: The validated TextSpliceRecording schema for the given text_splice_id, or `None` if no recording exists.
    """
    recording_db = (
        db.query(_models.TextSpliceRecording)
        .filter(_models.TextSpliceRecording.text_splice_id == text_splice_id)
        .first()
    )
    return (
        _schemas.TextSpliceRecording.model_validate(recording_db)
        if recording_db
        else None
    )


def seed_text_splices(db: "Session", prompts: list[str]) -> int:
    cleaned_prompts = [prompt.strip() for prompt in prompts if prompt and prompt.strip()]
    if not cleaned_prompts:
        return 0

    existing_rows = (
        db.query(_models.TextSplice.prompt_text)
        .filter(_models.TextSplice.prompt_text.in_(cleaned_prompts))
        .all()
    )
    existing_prompts = {row[0] for row in existing_rows}

    new_records = [
        _models.TextSplice(prompt_text=prompt, status="pending")
        for prompt in cleaned_prompts
        if prompt not in existing_prompts
    ]
    if not new_records:
        return 0

    db.bulk_save_objects(new_records)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(new_records)

async def create_high_quality_labeled_splice(
    splice: _schemas.HighQualityLabeledSpliceCreate, db: "Session") -> _schemas.HighQualityLabeledSplice:
    splice_db = _models.HighQualityLabeledSplice(**splice.model_dump())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.HighQualityLabeledSplice.model_validate(splice_db)

async def create_labeled_splice(
    splice: _schemas.LabeledSpliceCreate, db: "Session") -> _schemas.LabeledSplice:
    splice_db = _models.LabeledSplice(**splice.model_dump())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.LabeledSplice.model_validate(splice_db)

async def create_deleted_splice(
    splice: _schemas.DeletedSpliceCreate, db: "Session") -> _schemas.DeletedSplice:
    """
    Create and persist a DeletedSplice record and return the validated schema.
    
    Parameters:
        splice (_schemas.DeletedSpliceCreate): Data used to create the DeletedSplice record.
    
    Returns:
        _schemas.DeletedSplice: The created DeletedSplice as a validated schema.
    """
    splice_db = _models.DeletedSplice(**splice.model_dump())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.DeletedSplice.model_validate(splice_db)

def get_user(db: "Session", user_id: UUID):
    """
    Retrieve a User by its UUID.
    
    Returns:
        The matching User model instance if found, otherwise None.
    """
    return db.query(_models.User).filter(_models.User.id == user_id).first()

def get_user_by_email(db: "Session", email: str):
    """
    Retrieve a User by their email address.
    
    Parameters:
        email (str): Email address to look up (exact match).
    
    Returns:
        _models.User | None: The matching User model instance if found, otherwise `None`.
    """
    return db.query(_models.User).filter(_models.User.email == email).first()

def create_user(
    db: "Session", 
    user: _schemas.UserCreate, 
    hashed_password: str = None,
    verification_code: str = None,
    verification_code_expires = None
):
    """
    Create a new user record after validating the provided policy consent and return the created user as a validated schema.
    
    Validates that `user.consent_id` is present and refers to an existing PolicyConsent; removes any plaintext `password` from the input before creating the DB record. If `verification_code` is provided the created user will have `is_verified` set to `False`; otherwise `is_verified` is set to `True`. The `profile_completed` flag is set to `True` only when the resolved provider (normalized to lowercase) is `"system"`. The supplied `hashed_password` is stored on the created user record.
    
    Parameters:
        user (_schemas.UserCreate): User creation payload (must include `consent_id`).
        hashed_password (str, optional): Pre-hashed password to store on the user record.
        verification_code (str, optional): Verification code to associate with the user; presence marks the user unverified.
        verification_code_expires (datetime.date|datetime.datetime, optional): Expiration for the verification code.
    
    Returns:
        _schemas.User: The created user validated through the Pydantic schema.
    
    Raises:
        HTTPException: 400 if `consent_id` is missing or does not correspond to an existing PolicyConsent.
    """
    user_dict = user.model_dump()
    if 'password' in user_dict:
        del user_dict['password']

    consent_id = user_dict.get("consent_id")
    if consent_id is None:
        raise HTTPException(status_code=400, detail="consent_id is required")
    consent_record = get_policy_consent_by_id(db, consent_id)
    if consent_record is None:
        raise HTTPException(status_code=400, detail="Invalid consent_id")
    
    provider = (user_dict.get("provider") or "local").strip().lower()
    
    # Handle verification and profile completion fields
    user_db = _models.User(
        **user_dict, 
        hashed_password=hashed_password,
        verification_code=verification_code,
        verification_code_expires=verification_code_expires,
        is_verified=False if verification_code else True,  # Google users are auto-verified
        profile_completed=(provider == "system"),
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return _schemas.User.model_validate(user_db)


def anonymize_user(db: "Session", user: _models.User) -> _schemas.User:
    """
    Anonymizes personally identifiable information on a User model while preserving referential integrity.
    
    Parameters:
        user (_models.User): The SQLAlchemy User model instance to anonymize.
    
    Returns:
        anonymized_user (_schemas.User): The anonymized User as a validated schema.
    """
    placeholder_email = f"deleted+{user.id}@example.invalid"

    user.name = None
    user.surname = None
    user.email = placeholder_email
    user.phone_number = None
    user.age = None
    user.nationality = None
    user.accent = None
    user.region = None
    user.avatar_url = None
    user.hashed_password = None
    user.provider = "deleted"
    user.is_verified = False
    user.verification_code = None
    user.verification_code_expires = None
    user.reset_code = None
    user.reset_code_expires = None
    user.profile_completed = False
    user.token_version = (user.token_version or 0) + 1
    user.modified_at = _dt.datetime.utcnow()

    db.commit()
    db.refresh(user)
    return _schemas.User.model_validate(user)

def get_user_stats(db: "Session", user_id: UUID):
    """
    Compute activity and time metrics for a user across recording, labeling, and validation work.
    
    Parameters:
        user_id (UUID): The user's UUID to compute statistics for.
    
    Returns:
        dict: A mapping with the following keys:
            recorded_count (int): Number of TextSpliceRecordings created by the user.
            labeled_count (int): Number of LabeledSplice and HighQualityLabeledSplice entries labeled by the user (excludes auto-recorded clips and items already recorded).
            validated_count (int): Number of HighQualityLabeledSplice entries validated by the user.
            hours_recorded (float): Total recording duration in hours, rounded to 2 decimal places.
            hours_labeled (float): Total labeling duration in hours, rounded to 2 decimal places.
            hours_validated (float): Total validation duration in hours, rounded to 2 decimal places.
    """
    recording_name_pattern = "recordings_%"

    def sum_duration(query):
        """
        Compute the sum of `duration` values from an iterable of rows.
        
        Parameters:
        	query (Iterable): Iterable of objects or mappings with a `duration` attribute or key that can be converted to `float`. Non-numeric or missing durations are ignored.
        
        Returns:
        	total (float): Sum of all successfully converted `duration` values.
        """
        total = 0.0
        for row in query:
            try:
                total += float(row.duration)
            except (ValueError, TypeError):
                pass
        return total

    recorded_count = (
        db.query(func.count(_models.TextSpliceRecording.id))
        .filter(_models.TextSpliceRecording.labeler_id == user_id)
        .scalar()
        or 0
    )

    recorded_duration_query = (
        db.query(_models.TextSpliceRecording.duration)
        .filter(_models.TextSpliceRecording.labeler_id == user_id)
    )
    hours_recorded = sum_duration(recorded_duration_query) / 3600.0

    recorded_splice_ids_select = (
        select(_models.TextSpliceRecording.recorded_splice_id)
        .where(_models.TextSpliceRecording.recorded_splice_id.isnot(None))
    )

    # Labeled count: Exclude auto-recorded clips so recording work is tracked separately
    labeled_count = (
        db.query(func.count(_models.LabeledSplice.id))
        .filter(
            _models.LabeledSplice.labeler_id == user_id,
            _models.LabeledSplice.name.notlike(recording_name_pattern),
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_select),
        )
        .scalar()
        or 0
    )
    labeled_count += (
        db.query(func.count(_models.HighQualityLabeledSplice.id))
        .filter(
            _models.HighQualityLabeledSplice.labeler_id == user_id,
            _models.HighQualityLabeledSplice.name.notlike(recording_name_pattern),
        )
        .scalar()
        or 0
    )

    # Validated count: In HighQuality (validator_id)
    validated_count = (
        db.query(func.count(_models.HighQualityLabeledSplice.id))
        .filter(_models.HighQualityLabeledSplice.validator_id == user_id)
        .scalar()
        or 0
    )

    labeled_q1 = (
        db.query(_models.LabeledSplice.duration)
        .filter(
            _models.LabeledSplice.labeler_id == user_id,
            _models.LabeledSplice.name.notlike(recording_name_pattern),
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_select),
        )
    )
    labeled_q2 = (
        db.query(_models.HighQualityLabeledSplice.duration)
        .filter(
            _models.HighQualityLabeledSplice.labeler_id == user_id,
            _models.HighQualityLabeledSplice.name.notlike(recording_name_pattern),
        )
    )

    hours_labeled = (sum_duration(labeled_q1) + sum_duration(labeled_q2)) / 3600.0

    validated_q = db.query(_models.HighQualityLabeledSplice.duration).filter(_models.HighQualityLabeledSplice.validator_id == user_id)
    hours_validated = sum_duration(validated_q) / 3600.0

    stats = {
        "recorded_count": recorded_count,
        "labeled_count": labeled_count,
        "validated_count": validated_count,
        "hours_recorded": round(hours_recorded, 2),
        "hours_labeled": round(hours_labeled, 2),
        "hours_validated": round(hours_validated, 2),
    }
    stats.update(get_user_upload_stats(db, user_id))
    return stats


def get_user_upload_stats(db: "Session", user_id: UUID):
    """
    Aggregate splice generation metrics for the media a user has uploaded.

    Splices are tied to an upload through `UploadRecord.display_name` == `Splice.name`
    (the shared normalized video name), so this walks every splice queue for the
    user's upload names and totals how many segments were generated versus how many
    are still awaiting a label.

    Parameters:
        user_id (UUID): The user whose uploaded media should be aggregated.

    Returns:
        dict: A mapping with:
            uploaded_splices (int): Total splices generated across all of the user's uploads.
            unlabeled_splices (int): Generated splices that are still unlabeled.
            hours_uploaded (float): Total duration of every generated splice, in hours.
            hours_unlabeled (float): Duration of the unlabeled splices, in hours.
    """
    def _sum_duration(rows):
        total = 0.0
        for row in rows:
            try:
                total += float(row.duration)
            except (ValueError, TypeError):
                pass
        return total

    empty = {
        "uploaded_splices": 0,
        "unlabeled_splices": 0,
        "hours_uploaded": 0.0,
        "hours_unlabeled": 0.0,
    }

    upload_names = [
        row.display_name
        for row in (
            db.query(_models.UploadRecord.display_name)
            .filter(_models.UploadRecord.user_id == user_id)
            .all()
        )
        if row.display_name
    ]
    names = list(set(upload_names))
    if not names:
        return empty

    def _count_and_seconds(model, *extra_filters):
        query = db.query(model.duration).filter(
            model.owner_id == user_id,
            model.name.in_(names)
        )
        for extra in extra_filters:
            query = query.filter(extra)
        rows = query.all()
        return len(rows), _sum_duration(rows)
    unlabeled_c, unlabeled_s = _count_and_seconds(_models.Splice)
    labeled_c, labeled_s = _count_and_seconds(_models.LabeledSplice)
    validated_c, validated_s = _count_and_seconds(_models.HighQualityLabeledSplice)
    processing_c, processing_s = _count_and_seconds(_models.SpliceBeingProcessed)
    processing_unlabeled_c, processing_unlabeled_s = _count_and_seconds(
        _models.SpliceBeingProcessed,
        _models.SpliceBeingProcessed.status == "un_labeled",
    )

    generated_count = unlabeled_c + labeled_c + validated_c + processing_c
    generated_seconds = unlabeled_s + labeled_s + validated_s + processing_s
    still_unlabeled_count = unlabeled_c + processing_unlabeled_c
    still_unlabeled_seconds = unlabeled_s + processing_unlabeled_s

    return {
        "uploaded_splices": generated_count,
        "unlabeled_splices": still_unlabeled_count,
        "hours_uploaded": round(generated_seconds / 3600.0, 2),
        "hours_unlabeled": round(still_unlabeled_seconds / 3600.0, 2),
    }


def get_user_activity(db: "Session", user_id: UUID, page: int, page_size: int):
    """
    Return a paginated union of activity records for a user, combining labeled, pending validation, high-quality labeled, validated, and recorded items.
    
    Parameters:
        db (Session): Database session.
        user_id (UUID): User identifier to filter activity for.
        page (int): 1-based page number for pagination.
        page_size (int): Number of items per page.
    
    Returns:
        (total, rows): 
            total (int): Total number of activity rows for the user.
            rows (List[Row]): Paginated list of activity rows ordered by most recent activity. Each row contains:
                - id: item UUID
                - activity_type: one of "labeled", "validated", or "recorded"
                - name, path, label, origin, duration, validation
                - owner_id, labeler_id, validator_id
                - created_at: timestamp used for ordering
                - activity_rank: integer used to break ties when ordering
    """
    recording_name_pattern = "recordings_%"
    recorded_splice_ids_select = (
        select(_models.TextSpliceRecording.recorded_splice_id)
        .where(_models.TextSpliceRecording.recorded_splice_id.isnot(None))
    )

    labeled_stmt = (
        select(
            _models.LabeledSplice.id.label("id"),
            literal("labeled").label("activity_type"),
            _models.LabeledSplice.name,
            _models.LabeledSplice.path,
            _models.LabeledSplice.label,
            _models.LabeledSplice.origin,
            _models.LabeledSplice.duration,
            _models.LabeledSplice.validation,
            _models.LabeledSplice.owner_id,
            _models.LabeledSplice.labeler_id,
            literal(None).label("validator_id"),
            func.coalesce(_models.LabeledSplice.updated_at, _models.LabeledSplice.created_at).label("created_at"),
            literal(1).label("activity_rank"),
        )
        .where(
            _models.LabeledSplice.labeler_id == user_id,
            _models.LabeledSplice.name.notlike(recording_name_pattern),
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_select),
        )
    )

    pending_validation_stmt = (
        select(
            _models.SpliceBeingProcessed.id.label("id"),
            literal("labeled").label("activity_type"),
            _models.SpliceBeingProcessed.name,
            _models.SpliceBeingProcessed.path,
            _models.SpliceBeingProcessed.label,
            _models.SpliceBeingProcessed.origin,
            _models.SpliceBeingProcessed.duration,
            _models.SpliceBeingProcessed.validation,
            _models.SpliceBeingProcessed.owner_id,
            _models.SpliceBeingProcessed.labeler_id,
            _models.SpliceBeingProcessed.validator_id,
            func.coalesce(
                _models.SpliceBeingProcessed.updated_at,
                _models.SpliceBeingProcessed.created_at,
            ).label("created_at"),
            literal(2).label("activity_rank"),
        )
        .where(
            _models.SpliceBeingProcessed.status == "labeled",
            _models.SpliceBeingProcessed.labeler_id == user_id,
            _models.SpliceBeingProcessed.name.notlike(recording_name_pattern),
        )
    )

    high_quality_labeled_stmt = (
        select(
            _models.HighQualityLabeledSplice.id.label("id"),
            literal("labeled").label("activity_type"),
            _models.HighQualityLabeledSplice.name,
            _models.HighQualityLabeledSplice.path,
            _models.HighQualityLabeledSplice.label,
            _models.HighQualityLabeledSplice.origin,
            _models.HighQualityLabeledSplice.duration,
            _models.HighQualityLabeledSplice.validation,
            _models.HighQualityLabeledSplice.owner_id,
            _models.HighQualityLabeledSplice.labeler_id,
            _models.HighQualityLabeledSplice.validator_id,
            func.coalesce(
                _models.HighQualityLabeledSplice.updated_at,
                _models.HighQualityLabeledSplice.created_at,
            ).label("created_at"),
            literal(3).label("activity_rank"),
        )
        .where(
            _models.HighQualityLabeledSplice.labeler_id == user_id,
            _models.HighQualityLabeledSplice.name.notlike(recording_name_pattern),
        )
    )

    validated_stmt = (
        select(
            _models.HighQualityLabeledSplice.id.label("id"),
            literal("validated").label("activity_type"),
            _models.HighQualityLabeledSplice.name,
            _models.HighQualityLabeledSplice.path,
            _models.HighQualityLabeledSplice.label,
            _models.HighQualityLabeledSplice.origin,
            _models.HighQualityLabeledSplice.duration,
            _models.HighQualityLabeledSplice.validation,
            _models.HighQualityLabeledSplice.owner_id,
            _models.HighQualityLabeledSplice.labeler_id,
            _models.HighQualityLabeledSplice.validator_id,
            func.coalesce(
                _models.HighQualityLabeledSplice.updated_at,
                _models.HighQualityLabeledSplice.created_at,
            ).label("created_at"),
            literal(4).label("activity_rank"),
        )
        .where(_models.HighQualityLabeledSplice.validator_id == user_id)
    )

    recorded_stmt = (
        select(
            _models.TextSpliceRecording.id.label("id"),
            literal("recorded").label("activity_type"),
            _models.TextSpliceRecording.name,
            _models.TextSpliceRecording.path,
            _models.TextSpliceRecording.label,
            _models.TextSpliceRecording.origin,
            _models.TextSpliceRecording.duration,
            _models.TextSpliceRecording.validation,
            _models.TextSpliceRecording.owner_id,
            _models.TextSpliceRecording.labeler_id,
            literal(None).label("validator_id"),
            func.coalesce(
                _models.TextSpliceRecording.updated_at,
                _models.TextSpliceRecording.created_at,
            ).label("created_at"),
            literal(5).label("activity_rank"),
        )
        .where(_models.TextSpliceRecording.labeler_id == user_id)
    )

    union_subquery = union_all(
        labeled_stmt,
        pending_validation_stmt,
        high_quality_labeled_stmt,
        validated_stmt,
        recorded_stmt,
    ).subquery()

    total = db.query(func.count()).select_from(union_subquery).scalar() or 0

    rows = (
        db.query(union_subquery)
        .order_by(union_subquery.c.created_at.desc(), union_subquery.c.activity_rank)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, rows


def get_user_upload_records(db: "Session", user_id: UUID, page: int, page_size: int):
    """
    Retrieve paginated upload records for a user, ordered by creation time descending.
    
    Parameters:
        user_id (UUID): ID of the user whose upload records to query.
        page (int): 1-based page number to return.
        page_size (int): Number of records per page.
    
    Returns:
        tuple: (total, records) where `total` is the total count of matching UploadRecord rows (int) and `records` is a list of UploadRecord model instances for the requested page ordered by `created_at` descending.
    """
    base_query = (
        db.query(_models.UploadRecord)
        .filter(_models.UploadRecord.user_id == user_id)
        .order_by(_models.UploadRecord.created_at.desc())
    )
    total = base_query.count()
    records = (
        base_query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, records


def get_splice_stats_for_video_names(db: "Session", user_id: UUID, video_names: list[str]):
    """
    Aggregate splice counts per video name for a single owner.

    Splice ``name`` is derived from the user-supplied upload title and is not
    globally unique, so every query is additionally scoped by ``owner_id`` to
    avoid mixing in another user's splices that happen to share a name.

    Parameters:
        user_id (UUID): Owner whose splices should be counted.
        video_names (list[str]): Upload names to aggregate counts for.

    Returns:
        dict: Mapping of video name to ``{total_generated, validated_count,
        labeled_count, unlabeled_count}``.
    """
    if not video_names:
        return {}

    unique_names = set(filter(None, video_names))
    if not unique_names:
        return {}

    def _empty():
        return {
            "total_generated": 0,
            "validated_count": 0,
            "labeled_count": 0,
            "unlabeled_count": 0,
        }

    stats = {name: _empty() for name in unique_names}

    unlabeled_rows = (
        db.query(_models.Splice.name, func.count(_models.Splice.id))
        .filter(_models.Splice.owner_id == user_id, _models.Splice.name.in_(unique_names))
        .group_by(_models.Splice.name)
        .all()
    )
    for name, count in unlabeled_rows:
        bucket = stats.setdefault(name, _empty())
        bucket["unlabeled_count"] += count
        bucket["total_generated"] += count

    labeled_rows = (
        db.query(_models.LabeledSplice.name, func.count(_models.LabeledSplice.id))
        .filter(_models.LabeledSplice.owner_id == user_id, _models.LabeledSplice.name.in_(unique_names))
        .group_by(_models.LabeledSplice.name)
        .all()
    )
    for name, count in labeled_rows:
        bucket = stats.setdefault(name, _empty())
        bucket["labeled_count"] += count
        bucket["total_generated"] += count

    validated_rows = (
        db.query(_models.HighQualityLabeledSplice.name, func.count(_models.HighQualityLabeledSplice.id))
        .filter(_models.HighQualityLabeledSplice.owner_id == user_id, _models.HighQualityLabeledSplice.name.in_(unique_names))
        .group_by(_models.HighQualityLabeledSplice.name)
        .all()
    )
    for name, count in validated_rows:
        bucket = stats.setdefault(name, _empty())
        bucket["validated_count"] += count
        bucket["total_generated"] += count

    processing_rows = (
        db.query(
            _models.SpliceBeingProcessed.name,
            _models.SpliceBeingProcessed.status,
            func.count(_models.SpliceBeingProcessed.id),
        )
        .filter(_models.SpliceBeingProcessed.owner_id == user_id, _models.SpliceBeingProcessed.name.in_(unique_names))
        .group_by(_models.SpliceBeingProcessed.name, _models.SpliceBeingProcessed.status)
        .all()
    )
    for name, status, count in processing_rows:
        bucket = stats.setdefault(name, _empty())
        if status == "un_labeled":
            bucket["unlabeled_count"] += count
        elif status == "labeled":
            bucket["labeled_count"] += count
        bucket["total_generated"] += count

    return stats

