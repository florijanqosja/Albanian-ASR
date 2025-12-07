import datetime as _dt
from typing import TYPE_CHECKING, Optional

from fastapi import HTTPException
from sqlalchemy import func, literal, select, union_all

from . import database as _database
from . import models as _models
from . import schemas as _schemas
from .enums import MediaProcessingStatus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _add_tables():
    return _database.Base.metadata.create_all(bind=_database.engine)

SessionLocal = _database.SessionLocal

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_video(video: _schemas.VideoCreate, db: "Session") -> _schemas.Video:
    video_db = _models.Video(**video.model_dump())
    db.add(video_db)
    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)

async def update_video(video_path: str, update_data: dict, db: "Session") -> _schemas.Video:
    video_db = db.query(_models.Video).filter(_models.Video.path == video_path).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)


async def update_video_by_id(video_id: int, update_data: dict, db: "Session") -> _schemas.Video:
    video_db = db.query(_models.Video).filter(_models.Video.id == video_id).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.model_validate(video_db)

async def update_splice_being_processed(splice_id: int, data: dict, db: "Session") -> _schemas.SpliceBeingProcessed:
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

async def create_splice_being_processed(splice: _schemas.SpliceBeingProcessedCreate, db: "Session") -> _schemas.SpliceBeingProcessed:
    splice_dict = splice.model_dump()
    splice_being_processed_db = _models.SpliceBeingProcessed(**splice_dict)
    db.add(splice_being_processed_db)
    db.commit()
    db.refresh(splice_being_processed_db)
    return _schemas.SpliceBeingProcessed.model_validate(splice_being_processed_db)


async def create_upload_record(upload: _schemas.UploadRecordCreate, db: "Session") -> _schemas.UploadRecord:
    upload_db = _models.UploadRecord(**upload.model_dump())
    db.add(upload_db)
    db.commit()
    db.refresh(upload_db)
    return _schemas.UploadRecord.model_validate(upload_db)


def update_upload_record(upload_id: int, data: dict, db: "Session") -> _schemas.UploadRecord:
    record = db.query(_models.UploadRecord).filter(_models.UploadRecord.id == upload_id).first()
    if record is None:
        raise HTTPException(404, detail="Upload record not found")

    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return _schemas.UploadRecord.model_validate(record)


def set_upload_status(
    upload_id: int,
    status: MediaProcessingStatus,
    db: "Session",
    error_message: Optional[str] = None,
) -> _schemas.UploadRecord:
    payload = {"status": status}
    if error_message is not None:
        payload["error_message"] = error_message
    return update_upload_record(upload_id, payload, db)

async def delete_labeled_splice(splice_id: int, db: "Session"):
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

async def delete_splice(splice_id: int, db: "Session"):
    db.query(_models.Splice).filter(_models.Splice.id == splice_id).delete()
    db.commit()

async def get_first_labeled_splice(db: "Session") -> _schemas.LabeledSplice:
    first_splice = db.query(_models.LabeledSplice).order_by(_models.LabeledSplice.id).first()
    return _schemas.LabeledSplice.model_validate(first_splice) if first_splice else None

async def get_first_splice(db: "Session") -> _schemas.Splice:
    first_splice = db.query(_models.Splice).order_by(_models.Splice.id).first()
    return _schemas.Splice.model_validate(first_splice) if first_splice else None

async def get_splice_being_processed(splice_id: int, db: "Session") -> _schemas.SpliceBeingProcessed:
    return db.query(_models.SpliceBeingProcessed).get(splice_id)

async def delete_splice_being_processed(splice: _schemas.SpliceBeingProcessed, db: "Session") -> None:
    try:
        db.delete(splice)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_text_splice(text_splice: _schemas.TextSpliceCreate, db: "Session") -> _schemas.TextSplice:
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


async def update_text_splice(text_splice_id: int, update_data: dict, db: "Session") -> _schemas.TextSplice:
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


async def reserve_text_splice(text_splice_id: int, user_id: str, db: "Session") -> _schemas.TextSplice:
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


def get_text_splice_by_id(db: "Session", text_splice_id: int) -> Optional[_schemas.TextSplice]:
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.id == text_splice_id)
        .first()
    )
    return _schemas.TextSplice.model_validate(text_splice_db) if text_splice_db else None


def get_reserved_text_splice_for_user(db: "Session", user_id: str) -> Optional[_schemas.TextSplice]:
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
    text_splice_id: int,
    recorded_splice_id: Optional[int],
    db: "Session",
) -> _schemas.TextSplice:
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
    text_splice_db = (
        db.query(_models.TextSplice)
        .filter(_models.TextSplice.status == "pending")
        .order_by(_models.TextSplice.id)
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
    db: "Session", text_splice_id: int
) -> Optional[_schemas.TextSpliceRecording]:
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
    splice_db = _models.DeletedSplice(**splice.model_dump())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.DeletedSplice.model_validate(splice_db)

def get_user(db: "Session", user_id: str):
    return db.query(_models.User).filter(_models.User.id == user_id).first()

def get_user_by_email(db: "Session", email: str):
    return db.query(_models.User).filter(_models.User.email == email).first()

def create_user(
    db: "Session", 
    user: _schemas.UserCreate, 
    hashed_password: str = None,
    verification_code: str = None,
    verification_code_expires = None
):
    user_dict = user.model_dump()
    if 'password' in user_dict:
        del user_dict['password']
    
    # Generate UUID if not provided (though usually we let the DB or caller handle it, 
    # but here I'll generate it if I can import uuid, or rely on the caller)
    # The model defines id as String.
    import uuid
    if 'id' not in user_dict:
        user_dict['id'] = str(uuid.uuid4())
    
    # Determine if this is a local or Google user
    is_google_user = user_dict.get('provider') == 'google'
    
    # Handle verification and profile completion fields
    user_db = _models.User(
        **user_dict, 
        hashed_password=hashed_password,
        verification_code=verification_code,
        verification_code_expires=verification_code_expires,
        is_verified=False if verification_code else True,  # Google users are auto-verified
        profile_completed=not is_google_user  # Local users have completed profile, Google users need to complete it
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return _schemas.User.model_validate(user_db)

def get_user_stats(db: "Session", user_id: str):
    recording_name_pattern = "recordings_%"

    def sum_duration(query):
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

    recorded_splice_ids_subquery = (
        select(_models.TextSpliceRecording.recorded_splice_id)
        .where(_models.TextSpliceRecording.recorded_splice_id.isnot(None))
        .subquery()
    )

    # Labeled count: Exclude auto-recorded clips so recording work is tracked separately
    labeled_count = (
        db.query(func.count(_models.LabeledSplice.id))
        .filter(
            _models.LabeledSplice.labeler_id == user_id,
            _models.LabeledSplice.name.notlike(recording_name_pattern),
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_subquery),
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
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_subquery),
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

    return {
        "recorded_count": recorded_count,
        "labeled_count": labeled_count,
        "validated_count": validated_count,
        "hours_recorded": round(hours_recorded, 2),
        "hours_labeled": round(hours_labeled, 2),
        "hours_validated": round(hours_validated, 2),
    }

def get_user_activity(db: "Session", user_id: str, page: int, page_size: int):
    recording_name_pattern = "recordings_%"
    recorded_splice_ids_subquery = (
        select(_models.TextSpliceRecording.recorded_splice_id)
        .subquery()
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
            (_models.LabeledSplice.id * 10 + 1).label("sort_key"),
        )
        .where(
            _models.LabeledSplice.labeler_id == user_id,
            _models.LabeledSplice.name.notlike(recording_name_pattern),
            ~_models.LabeledSplice.id.in_(recorded_splice_ids_subquery),
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
            (_models.SpliceBeingProcessed.id * 10 + 2).label("sort_key"),
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
            (_models.HighQualityLabeledSplice.id * 10 + 3).label("sort_key"),
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
            (_models.HighQualityLabeledSplice.id * 10 + 4).label("sort_key"),
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
            (_models.TextSpliceRecording.id * 10 + 5).label("sort_key"),
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
        .order_by(union_subquery.c.sort_key.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, rows


def get_user_upload_records(db: "Session", user_id: str, page: int, page_size: int):
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


def get_splice_stats_for_video_names(db: "Session", video_names: list[str]):
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
        .filter(_models.Splice.name.in_(unique_names))
        .group_by(_models.Splice.name)
        .all()
    )
    for name, count in unlabeled_rows:
        bucket = stats.setdefault(name, _empty())
        bucket["unlabeled_count"] += count
        bucket["total_generated"] += count

    labeled_rows = (
        db.query(_models.LabeledSplice.name, func.count(_models.LabeledSplice.id))
        .filter(_models.LabeledSplice.name.in_(unique_names))
        .group_by(_models.LabeledSplice.name)
        .all()
    )
    for name, count in labeled_rows:
        bucket = stats.setdefault(name, _empty())
        bucket["labeled_count"] += count
        bucket["total_generated"] += count

    validated_rows = (
        db.query(_models.HighQualityLabeledSplice.name, func.count(_models.HighQualityLabeledSplice.id))
        .filter(_models.HighQualityLabeledSplice.name.in_(unique_names))
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
        .filter(_models.SpliceBeingProcessed.name.in_(unique_names))
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


