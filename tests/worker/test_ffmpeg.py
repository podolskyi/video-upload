# -*- coding=utf-8 -*-
import logging
from unittest import TestCase
from unittest.mock import Mock, patch

from video_upload.worker.ffmpeg import (
    handle_uploaded_media_file, UploadedMediaFileState, MediaFile,
    convert_uploaded_media_file,
    upload_media_file_variant, UploadedMediaFile, Blob,
)

logger = logging.getLogger(__name__)


class HandleUploadedMediaFileTestCase(TestCase):
    @patch("video_upload.worker.ffmpeg.db")
    @patch("video_upload.worker.ffmpeg.ffprobe")
    def test_bad_probe(self, ffprobe, db):
        ffprobe.return_value = None
        uploaded_media_file = Mock()

        handle_uploaded_media_file(uploaded_media_file)

        ffprobe.assert_called_once_with(uploaded_media_file.tmp_path)
        self.assertEqual(uploaded_media_file.state, UploadedMediaFileState.ERROR)
        db.session.commit.assert_called_once_with()

    @patch("video_upload.worker.ffmpeg.db")
    @patch("video_upload.worker.ffmpeg.ffprobe")
    @patch("video_upload.worker.ffmpeg.get_probe_video_stream")
    def test_no_video_stream(self, get_probe_video_stream, ffprobe, db):
        get_probe_video_stream.return_value = None
        uploaded_media_file = Mock()

        handle_uploaded_media_file(uploaded_media_file)

        ffprobe.assert_called_once_with(uploaded_media_file.tmp_path)
        get_probe_video_stream.assert_called_once_with(ffprobe.return_value)
        self.assertEqual(uploaded_media_file.state, UploadedMediaFileState.ERROR)
        db.session.commit.assert_called_once_with()

    @patch("video_upload.worker.ffmpeg.db")
    @patch("video_upload.worker.ffmpeg.ffprobe")
    @patch("video_upload.worker.ffmpeg.get_probe_video_stream")
    @patch("video_upload.worker.ffmpeg.convert_uploaded_media_file")
    def test_success(self, convert_uploaded_media_file, get_probe_video_stream, ffprobe, db):
        uploaded_media_file = Mock()

        handle_uploaded_media_file(uploaded_media_file)

        self.assertEqual(uploaded_media_file.state, UploadedMediaFileState.CONVERTING)
        self.assertIsInstance(uploaded_media_file.media_file, MediaFile)
        self.assertEqual(uploaded_media_file.media_file.probe, ffprobe.return_value)
        db.session.commit.assert_called_once_with()

        convert_uploaded_media_file.assert_called_once_with(uploaded_media_file)


class ConvertUploadedMediaFileTestCase(TestCase):
    @patch("video_upload.worker.ffmpeg.app")
    @patch("video_upload.worker.ffmpeg.ffmpeg_convert_file")
    @patch("video_upload.worker.ffmpeg.os")
    @patch("video_upload.worker.ffmpeg.upload_media_file_variant")
    def test_convert_success(self, upload_media_file_variant, os, ffmpeg_convert_file, app):
        app.config = {
            "MEDIA_FILE_VARIANTS": {
                "720p": {
                    "ffmpeg_arguments": Mock(),
                    "ext": "mp4",
                }
            }
        }
        uploaded_media_file = Mock()
        uploaded_media_file.tmp_path = "/tmp/video0000"

        convert_uploaded_media_file(uploaded_media_file)

        ffmpeg_convert_file.assert_called_once_with("/tmp/video0000",
                                                    app.config["MEDIA_FILE_VARIANTS"]["720p"]["ffmpeg_arguments"],
                                                    "/tmp/video0000-720p.mp4")
        os.unlink.assert_not_called()
        upload_media_file_variant.delay.assert_called_once_with(uploaded_media_file.media_file.id, "720p",
                                                                "/tmp/video0000-720p.mp4")


    @patch("video_upload.worker.ffmpeg.app")
    @patch("video_upload.worker.ffmpeg.ffmpeg_convert_file")
    @patch("video_upload.worker.ffmpeg.os")
    @patch("video_upload.worker.ffmpeg.upload_media_file_variant")
    def test_convert_error(self, upload_media_file_variant, os, ffmpeg_convert_file, app):
        app.config = {
            "MEDIA_FILE_VARIANTS": {
                "720p": {
                    "ffmpeg_arguments": Mock(),
                    "ext": "mp4",
                }
            }
        }
        uploaded_media_file = Mock()
        uploaded_media_file.tmp_path = "/tmp/video0000"
        ffmpeg_convert_file.side_effect = Exception()

        convert_uploaded_media_file(uploaded_media_file)

        ffmpeg_convert_file.assert_called_once_with("/tmp/video0000",
                                                    app.config["MEDIA_FILE_VARIANTS"]["720p"]["ffmpeg_arguments"],
                                                    "/tmp/video0000-720p.mp4")
        os.unlink.assert_called_once_with("/tmp/video0000-720p.mp4")


class UploadMediaFileVariantTestCase(TestCase):
    @patch("video_upload.worker.ffmpeg.app")
    @patch("video_upload.worker.ffmpeg.db")
    @patch("video_upload.worker.ffmpeg.ffprobe")
    @patch("video_upload.worker.ffmpeg.shutil")
    @patch("video_upload.worker.ffmpeg.uuid4")
    def test_upload_success(self, uuid4, shutil, ffprobe, db, app):
        media_file = MediaFile()
        uploaded_media_file = UploadedMediaFile()

        app.config = {
            "AZURE_ACCOUNT_NAME": "account-name",
            "AZURE_ACCOUNT_KEY": "account-key",
            "AZURE_CONTAINER_NAME": "container-name",

            "MEDIA_FILE_VARIANTS": {
                "720p": {
                    "ffmpeg_arguments": Mock(),
                    "ext": "mp4",
                    "content_type": "video/mp4",
                }
            },
            "MEDIA_FILES_PATH": "/media",
        }
        db.session.query = Mock(return_value=Mock(
            get=Mock(return_value=media_file),
            filter=Mock(return_value=[uploaded_media_file]),
        ))
        uuid4.return_value = "99082196-af0f-4c44-bdca-c83b02080ac8"

        upload_media_file_variant(1, "720p", "/tmp/video0000-720p.mp4")

        shutil.move.assert_called_once_with(
            "/tmp/video0000-720p.mp4",
            "/media/99082196-af0f-4c44-bdca-c83b02080ac8.mp4",
        )

        self.assertEqual(media_file.variants[0].variant_name, "720p")

        self.assertIsInstance(media_file.variants[0].blob, Blob)
        self.assertEqual(media_file.variants[0].blob.name, "99082196-af0f-4c44-bdca-c83b02080ac8.mp4")

        self.assertEqual(uploaded_media_file.state, UploadedMediaFileState.READY)

        db.session.commit.assert_called_once_with()
