import datetime as _dt
from typing import Optional
import pydantic as _pydantic


class _BaseContact(_pydantic.BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str

class Contact(_BaseContact):
    id: int
    date_created: _dt.datetime

    class Config:
        orm_mode = True

class CreateContact(_BaseContact):
    pass

class _BaseViedo(_pydantic.BaseModel):
    Vid_NAME: Optional[str]
    Vid_PATH: Optional[str]
    Vid_CATEGORY: Optional[str]
    Vid_TO_MP3_STATUS: Optional[str]
    Vid_SPLICE_STATUS: Optional[str]
    mp3_path: Optional[str]

class Video(_BaseViedo):
    Vid_ID: int
    Vid_UPLOAD_TIME: _dt.datetime

    class Config:
        orm_mode = True

class CreateVideo(_BaseViedo):
    pass

class _BaseSplice(_pydantic.BaseModel):
    Sp_NAME: str
    Sp_PATH: str
    Sp_LABEL: str
    Sp_ORIGIN: str
    Sp_DURATION: str
    Sp_VALIDATION: str


class Splice_table(_BaseSplice):
    Sp_ID: int

    class Config:
        orm_mode = True

class CreateSplice(_BaseSplice):
    pass



class _BaseLabeledSplie(_pydantic.BaseModel):
    Sp_NAME: str
    Sp_PATH: str
    Sp_LABEL: str
    Sp_ORIGIN: str
    Sp_DURATION: str
    Sp_VALIDATION: str


class Labeled_splice_table(_BaseLabeledSplie):
    Sp_ID: int

    class Config:
        orm_mode = True

class CreateHighQualityLabeledSplice(_BaseLabeledSplie):
    pass


class _BaseHighQualityLabeledSplie(_pydantic.BaseModel):
    Sp_NAME: str
    Sp_PATH: str
    Sp_LABEL: str
    Sp_ORIGIN: str
    Sp_DURATION: str
    Sp_VALIDATION: str


class High_quality_labeled_splice_table(_BaseHighQualityLabeledSplie):
    Sp_ID: int

    class Config:
        orm_mode = True

class CreateHighQualtyLabeledSplice(_BaseHighQualityLabeledSplie):
    pass


class _BaseSpliceBeeingProcessed(_pydantic.BaseModel):
    Sp_NAME: str
    Sp_PATH: str
    Sp_LABEL: str
    Sp_ORIGIN: str
    Sp_DURATION: str
    Sp_VALIDATION: str


class Splice_beeing_processed_table(_BaseSpliceBeeingProcessed):
    Sp_ID: int

    class Config:
        orm_mode = True

class CreateSpliceBeingProcessed(_BaseSpliceBeeingProcessed):
    pass