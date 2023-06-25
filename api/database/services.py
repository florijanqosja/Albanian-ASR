from typing import TYPE_CHECKING, List

from fastapi import HTTPException

from . import database as _database
from . import models as _models
from . import schemas as _schemas

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _add_tables():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_video(video: _schemas.CreateVideo, db: "Session") -> _schemas.Video:
    video_db = _models.Video_table(**video)
    db.add(video_db)
    db.commit()
    db.refresh(video_db)
    return _schemas.Video.from_orm(video_db)

async def update_video(video_path: str, update_data: dict, db: "Session") -> _schemas.Video:
    video_db = db.query(_models.Video_table).filter(_models.Video_table.Vid_PATH == video_path).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.from_orm(video_db)

async def update_splice_being_processed(Sp_ID: str, data: dict, db: "Session") -> _schemas.Splice_beeing_processed_table:
    splice_being_processed_db = db.query(_models.Splice_beeing_processed_table).filter(_models.Splice_beeing_processed_table.Sp_ID == Sp_ID).first()
    if splice_being_processed_db is None:
        raise HTTPException(404, detail="Splice not found")

    for key, value in data.items():
        setattr(splice_being_processed_db, key, value)

    db.commit()
    db.refresh(splice_being_processed_db)
    return _schemas.Splice_beeing_processed_table.from_orm(splice_being_processed_db)

async def create_splice(splice: _schemas.CreateSplice, db: "Session") -> _schemas.Splice_table:
    splice_db = _models.Splice_table(**splice)
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.Splice_table.from_orm(splice_db)

async def create_splice_being_processed(splice: _schemas.CreateSpliceBeingProcessed, db: "Session") -> _schemas.Splice_beeing_processed_table:
    splice_dict = splice.dict()
    splice_being_processed_db = _models.Splice_beeing_processed_table(**splice_dict)
    db.add(splice_being_processed_db)
    db.commit()
    db.refresh(splice_being_processed_db)
    return _schemas.Splice_beeing_processed_table.from_orm(splice_being_processed_db)

async def delete_labeled_splice(splice_id: int, db: "Session"):
    db.query(_models.Labeled_splice_table).filter(_models.Labeled_splice_table.Sp_ID == splice_id).delete()
    db.commit()

async def delete_splice(splice_id: int, db: "Session"):
    db.query(_models.Splice_table).filter(_models.Splice_table.Sp_ID == splice_id).delete()
    db.commit()

async def get_first_labeled_splice(db: "Session") -> _schemas.Labeled_splice_table:
    first_splice = db.query(_models.Labeled_splice_table).order_by(_models.Labeled_splice_table.Sp_ID).first()
    return _schemas.Labeled_splice_table.from_orm(first_splice) if first_splice else None

async def get_first_splice(db: "Session") -> _schemas.Splice_table:
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    return _schemas.Splice_table.from_orm(first_splice) if first_splice else None

async def get_splice_being_processed(splice_id: int, db: "Session") -> _schemas.Splice_beeing_processed_table:
    return db.query(_models.Splice_beeing_processed_table).get(splice_id)

async def delete_splice_being_processed(splice: _schemas.Splice_beeing_processed_table, db: "Session") -> None:
    try:
        db.delete(splice)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_high_quality_labeled_splice(
    splice: _schemas.CreateHighQualityLabeledSplice, db: "Session") -> _schemas.High_quality_labeled_splice_table:
    splice_db = _models.High_quality_labeled_splice_table(**splice.dict())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.High_quality_labeled_splice_table.from_orm(splice_db)

async def create_labeled_splice(
    splice: _schemas.CreateLabeledSplice, db: "Session") -> _schemas.Labeled_splice_table:
    splice_db = _models.Labeled_splice_table(**splice.dict())
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.Labeled_splice_table.from_orm(splice_db)

