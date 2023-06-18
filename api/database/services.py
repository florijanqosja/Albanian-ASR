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


async def create_contact(
    contact: _schemas.CreateContact, db: "Session"
) -> _schemas.Contact:
    contact = _models.Contact(**contact.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return _schemas.Contact.from_orm(contact)

async def create_video(video: _schemas.CreateVideo, db: "Session") -> _schemas.Video:
    video_db = _models.Video_table(**video)
    db.add(video_db)
    db.commit()
    db.refresh(video_db)
    return _schemas.Video.from_orm(video_db)

async def create_splice(splice: _schemas.CreateSplice, db: "Session") -> _schemas.Splice:
    splice_db = _models.Splice_table(**splice)
    db.add(splice_db)
    db.commit()
    db.refresh(splice_db)
    return _schemas.Splice.from_orm(splice_db)


# async def create_splice(splice_data: dict, db: "Session") -> _schemas.Splice:
#     splice_db = _models.Splice(**splice_data)
#     db.add(splice_db)
#     db.commit()
#     db.refresh(splice_db)
#     return _schemas.Splice.from_orm(splice_db)

async def update_video(video_path: str, update_data: dict, db: "Session") -> _schemas.Video:
    video_db = db.query(_models.Video_table).filter(_models.Video_table.Vid_PATH == video_path).first()
    if video_db is None:
        raise HTTPException(404, detail="Video not found")

    for key, value in update_data.items():
        setattr(video_db, key, value)

    db.commit()
    db.refresh(video_db)
    return _schemas.Video.from_orm(video_db)

async def get_all_contacts(db: "Session") -> List[_schemas.Contact]:
    contacts = db.query(_models.Contact).all()
    return list(map(_schemas.Contact.from_orm, contacts))


async def get_contact(contact_id: int, db: "Session"):
    contact = db.query(_models.Contact).filter(_models.Contact.id == contact_id).first()
    return contact


async def delete_contact(contact: _models.Contact, db: "Session"):
    db.delete(contact)
    db.commit()


async def update_contact(
    contact_data: _schemas.CreateContact, contact: _models.Contact, db: "Session"
) -> _schemas.Contact:
    contact.first_name = contact_data.first_name
    contact.last_name = contact_data.last_name
    contact.email = contact_data.email
    contact.phone_number = contact_data.phone_number

    db.commit()
    db.refresh(contact)

    return _schemas.Contact.from_orm(contact)