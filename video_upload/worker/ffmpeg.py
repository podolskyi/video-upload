from celery.exceptions import MaxRetriesExceededError
import json
import logging
import os
import shutil
import subprocess
from uuid import uuid4

from video_upload.app import app
from video_upload.celery import celery, exponential_backoff_countdown
from video_upload.db import db
from video_upload.models import *

logger = logging.getLogger(__name__)


@celery.task()
def process_uploaded_media_file(uploaded_media_file_id):
    uploaded_media_file = db.session.query(UploadedMediaFile).get(uploaded_media_file_id)
    if uploaded_media_file is None:
        logger.error("uploaded_media_file_id=%r does not exist", uploaded_media_file_id)
        return

    try:
        handle_uploaded_media_file(uploaded_media_file)
    finally:
        os.unlink(uploaded_media_file.tmp_path)


def handle_uploaded_media_file(uploaded_media_file):
    probe = ffprobe(uploaded_media_file.tmp_path)
    if probe is None:
        uploaded_media_file.state = UploadedMediaFileState.ERROR
        db.session.commit()
        return

    video_stream = get_probe_video_stream(probe)
    if video_stream is None:
        uploaded_media_file.state = UploadedMediaFileState.ERROR
        db.session.commit()
        return

    uploaded_media_file.state = UploadedMediaFileState.CONVERTING
    uploaded_media_file.media_file = MediaFile()
    uploaded_media_file.media_file.probe = probe
    db.session.commit()

    convert_uploaded_media_file(uploaded_media_file)


def ffprobe(path):
    try:
        return json.loads(subprocess.check_output(["ffprobe",
                                                   "-v", "0",
                                                   "-show_streams",
                                                   "-of", "json",
                                                   path]).decode("utf-8"))
    except (subprocess.CalledProcessError, ValueError):
        logger.info("ffprobe failed", exc_info=True)
        return None


def get_probe_video_stream(probe):
    for stream in probe["streams"]:
        if stream["codec_type"] == "video":
            return stream


def convert_uploaded_media_file(uploaded_media_file):
    for variant_name, variant in app.config["MEDIA_FILE_VARIANTS"].items():
        variant_tmp_path = "%s-%s.%s" % (uploaded_media_file.tmp_path, variant_name, variant["ext"])

        try:
            ffmpeg_convert_file(uploaded_media_file.tmp_path, variant["ffmpeg_arguments"], variant_tmp_path)
        except Exception:
            logger.info("ffmpeg failed", exc_info=True)
            try:
                os.unlink(variant_tmp_path)
            except Exception:
                pass
        else:
            upload_media_file_variant.delay(uploaded_media_file.media_file.id, variant_name, variant_tmp_path)


def ffmpeg_convert_file(src, arguments, dst):
    subprocess.check_call(["ffmpeg",
                           "-y",
                           "-loglevel", "quiet",
                           "-i", src] +
                          arguments +
                          [dst])


@celery.task(acks_late=True, bind=True, max_retries=None)
def upload_media_file_variant(self, media_file_id, variant_name, variant_tmp_path):
    media_file = db.session.query(MediaFile).get(media_file_id)
    if media_file_id is None:
        logger.error("media_file_id=%r does not exist", media_file_id)
        return

    variant = app.config["MEDIA_FILE_VARIANTS"][variant_name]

    probe = ffprobe(variant_tmp_path)
    if probe is None:
        os.unlink(variant_tmp_path)
        raise Exception("Got bad variant %r for media_file %r" % (variant_name, media_file.id))

    media_file_variant = MediaFileVariant()
    media_file_variant.variant_name = variant_name
    media_file_variant.media_file = media_file
    media_file_variant.probe = probe
    media_file_variant.blob = Blob()
    media_file_variant.blob.name = "%s.%s" % (uuid4(), variant["ext"])

    try:
        shutil.move(variant_tmp_path, os.path.join(app.config["MEDIA_FILES_PATH"], media_file_variant.blob.name))
    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=exponential_backoff_countdown(self))
        except MaxRetriesExceededError:
            os.unlink(variant_tmp_path)
            raise Exception("MaxRetriesExceededError happened on variant %r for media fire %r" % (variant, media_file.id))

    for uploaded_media_file in (
        db.session.query(UploadedMediaFile).
            filter(UploadedMediaFile.media_file == media_file)
    ):
        uploaded_media_file.state = UploadedMediaFileState.READY

    db.session.commit()
