import datetime as _dt
from typing import Optional, Generic, TypeVar, Any
import pydantic as _pydantic

T = TypeVar('T')

class ResponseModel(_pydantic.BaseModel, Generic[T]):
    status: str
    data: Optional[T] = None
    message: Optional[str] = None


class VideoBase(_pydantic.BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    category: Optional[str] = None
    to_mp3_status: Optional[str] = None
    splice_status: Optional[str] = None
    mp3_path: Optional[str] = None

class Video(VideoBase):
    id: int
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

class Splice(SpliceBase):
    id: int
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

class LabeledSplice(LabeledSpliceBase):
    id: int
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

class HighQualityLabeledSplice(HighQualityLabeledSpliceBase):
    id: int
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

class DeletedSplice(DeletedSpliceBase):
    id: int
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
    status: str

class SpliceBeingProcessed(SpliceBeingProcessedBase):
    id: int
    model_config = _pydantic.ConfigDict(from_attributes=True)

class SpliceBeingProcessedCreate(SpliceBeingProcessedBase):
    pass



class LabelSplice(_pydantic.BaseModel):
    id: int
    label: str
    validation: Optional[str] = None

class ValidateSplice(_pydantic.BaseModel):
    id: int
    label: str
    validation: Optional[str] = None

class DeleteSplice(_pydantic.BaseModel):
    id: int
