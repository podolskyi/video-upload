import enum
from sqlalchemy_enum34 import EnumType
from sqlalchemy.dialects.postgresql import JSONB

from video_upload.db import db

__all__ = ["UploadedMediaFileState", "UploadedMediaFile", "MediaFile", "MediaFileVariant", "Blob"]


class UploadedMediaFileState(enum.Enum):
    PROCESSING = "processing"
    CONVERTING = "converting"
    READY = "ready"
    ERROR = "error"


class UploadedMediaFile(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    state = db.Column(EnumType(UploadedMediaFileState, name="uploaded_media_file_state"))
    tmp_path = db.Column(db.Text(), nullable=True)
    media_file_id = db.Column(db.Integer(), db.ForeignKey("media_file.id"), nullable=True)

    media_file = db.relationship("MediaFile", foreign_keys=[media_file_id])


class MediaFile(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    probe = db.Column(JSONB())


class MediaFileVariant(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    variant_name = db.Column(db.Text())
    media_file_id = db.Column(db.Integer(), db.ForeignKey("media_file.id"))
    probe = db.Column(JSONB())
    blob_id = db.Column(db.Integer(), db.ForeignKey("blob.id"))

    media_file = db.relationship("MediaFile", foreign_keys=[media_file_id], backref=db.backref("variants"))
    blob = db.relationship("Blob", foreign_keys=[blob_id])

    __table_args__ = (
        db.UniqueConstraint(variant_name, media_file_id, name="ix__media_file_variant__variant_name__media_file_id"),
    )


class Blob(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Text())
