import datetime as _dt
import sqlalchemy as _sql

from . import database as _database


class Contact(_database.Base):
    __tablename__ = "contacts"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    first_name = _sql.Column(_sql.String, index=True)
    last_name = _sql.Column(_sql.String, index=True)
    email = _sql.Column(_sql.String, index=True, unique=True)
    phone_number = _sql.Column(_sql.String, index=True, unique=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

class Video_table(_database.Base):
    __tablename__ = "video_table"
    Vid_ID = _sql.Column(_sql.Integer, primary_key=True, index=True)
    Vid_NAME = _sql.Column(_sql.String, nullable=True)
    Vid_PATH = _sql.Column(_sql.String, nullable=True)
    Vid_CATEGORY = _sql.Column(_sql.String, nullable=True)
    Vid_TO_MP3_STATUS = _sql.Column(_sql.String, nullable=True)
    Vid_SPLICE_STATUS = _sql.Column(_sql.String, nullable=True)
    mp3_path = _sql.Column(_sql.String, nullable=True)
    Vid_UPLOAD_TIME = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

class Splice_table(_database.Base):
    __tablename__ = "splice_table"
    Sp_ID = _sql.Column(_sql.Integer, primary_key=True, index=True)
    Sp_NAME = _sql.Column(_sql.String, nullable=True)
    Sp_PATH = _sql.Column(_sql.String, nullable=True)
    Sp_LABEL = _sql.Column(_sql.String, nullable=True)
    Sp_ORIGIN = _sql.Column(_sql.String, nullable=True)
    Sp_DURATION = _sql.Column(_sql.String, nullable=True)
    Sp_VALIDATION = _sql.Column(_sql.String, nullable=True)

class Labeled_splice_table(_database.Base):
    __tablename__ = "labeled_splice_table"
    Sp_ID = _sql.Column(_sql.Integer, primary_key=True, index=True)
    Sp_NAME = _sql.Column(_sql.String, nullable=True)
    Sp_PATH = _sql.Column(_sql.String, nullable=True)
    Sp_LABEL = _sql.Column(_sql.String, nullable=True)
    Sp_ORIGIN = _sql.Column(_sql.String, nullable=True)
    Sp_DURATION = _sql.Column(_sql.String, nullable=True)
    Sp_VALIDATION = _sql.Column(_sql.String, nullable=True)

class High_quality_labeled_splice_table(_database.Base):
    __tablename__ = "high_quality_labeled_splice_table"
    Sp_ID = _sql.Column(_sql.Integer, primary_key=True, index=True)
    Sp_NAME = _sql.Column(_sql.String, nullable=True)
    Sp_PATH = _sql.Column(_sql.String, nullable=True)
    Sp_LABEL = _sql.Column(_sql.String, nullable=True)
    Sp_ORIGIN = _sql.Column(_sql.String, nullable=True)
    Sp_DURATION = _sql.Column(_sql.String, nullable=True)
    Sp_VALIDATION = _sql.Column(_sql.String, nullable=True)

class Deleted_splice_table(_database.Base):
    __tablename__ = "deleted_splice_table"
    Sp_ID = _sql.Column(_sql.Integer, primary_key=True, index=True)
    Sp_NAME = _sql.Column(_sql.String, nullable=True)
    Sp_PATH = _sql.Column(_sql.String, nullable=True)
    Sp_LABEL = _sql.Column(_sql.String, nullable=True)
    Sp_ORIGIN = _sql.Column(_sql.String, nullable=True)
    Sp_DURATION = _sql.Column(_sql.String, nullable=True)
    Sp_VALIDATION = _sql.Column(_sql.String, nullable=True)