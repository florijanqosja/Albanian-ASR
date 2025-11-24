import datetime as _dt
import sqlalchemy as _sql

from . import database as _database


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

class Splice(_database.Base):
    __tablename__ = "splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)

class LabeledSplice(_database.Base):
    __tablename__ = "labeled_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)

class HighQualityLabeledSplice(_database.Base):
    __tablename__ = "high_quality_labeled_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)

class DeletedSplice(_database.Base):
    __tablename__ = "deleted_splices"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=True)
    path = _sql.Column(_sql.String, nullable=True)
    label = _sql.Column(_sql.String, nullable=True)
    origin = _sql.Column(_sql.String, nullable=True)
    duration = _sql.Column(_sql.String, nullable=True)
    validation = _sql.Column(_sql.String, nullable=True)

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
