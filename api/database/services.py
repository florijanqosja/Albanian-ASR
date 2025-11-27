from typing import TYPE_CHECKING, List

from fastapi import HTTPException

from . import database as _database
from . import models as _models
from . import schemas as _schemas

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

async def delete_labeled_splice(splice_id: int, db: "Session"):
    db.query(_models.LabeledSplice).filter(_models.LabeledSplice.id == splice_id).delete()
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
    # Labeled count: In LabeledSplice (user_id) + In HighQuality (labeler_id)
    labeled_count = db.query(_models.LabeledSplice).filter(_models.LabeledSplice.user_id == user_id).count()
    labeled_count += db.query(_models.HighQualityLabeledSplice).filter(_models.HighQualityLabeledSplice.labeler_id == user_id).count()
    
    # Validated count: In HighQuality (user_id)
    validated_count = db.query(_models.HighQualityLabeledSplice).filter(_models.HighQualityLabeledSplice.user_id == user_id).count()
    
    # Calculate hours (simplified, assuming duration is float string)
    # This is inefficient for large datasets, should be done with SQL sum cast
    # But for now:
    
    def sum_duration(query):
        total = 0.0
        for row in query:
            try:
                total += float(row.duration)
            except (ValueError, TypeError):
                pass
        return total

    labeled_q1 = db.query(_models.LabeledSplice.duration).filter(_models.LabeledSplice.user_id == user_id)
    labeled_q2 = db.query(_models.HighQualityLabeledSplice.duration).filter(_models.HighQualityLabeledSplice.labeler_id == user_id)
    
    hours_labeled = (sum_duration(labeled_q1) + sum_duration(labeled_q2)) / 3600.0
    
    validated_q = db.query(_models.HighQualityLabeledSplice.duration).filter(_models.HighQualityLabeledSplice.user_id == user_id)
    hours_validated = sum_duration(validated_q) / 3600.0
    
    return {
        "labeled_count": labeled_count,
        "validated_count": validated_count,
        "hours_labeled": round(hours_labeled, 2),
        "hours_validated": round(hours_validated, 2)
    }

def get_user_activity(db: "Session", user_id: str, limit: int = 10):
    # Fetch recent activity from HighQualityLabeledSplice (completed items)
    # We could also include LabeledSplice (pending items) but let's start with completed.
    items = db.query(_models.HighQualityLabeledSplice).filter(
        (_models.HighQualityLabeledSplice.user_id == user_id) | 
        (_models.HighQualityLabeledSplice.labeler_id == user_id)
    ).order_by(_models.HighQualityLabeledSplice.id.desc()).limit(limit).all()
    return items


