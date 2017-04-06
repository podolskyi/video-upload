# -*- coding=utf-8 -*-
import logging
from unittest.mock import patch

from video_upload.db import db
from video_upload.models import UploadedMediaFile, UploadedMediaFileState
from video_upload.utils.integration_test_case import IntegrationTestCase

logger = logging.getLogger(__name__)


class UploadTestCase(IntegrationTestCase):
    @patch("video_upload.api.uploads.process_uploaded_media_file")
    def test_upload(self, process_uploaded_media_file):
        self.assertEqual(self.post("/api/v1/media_files/uploads/upload", {"file.path": "/tmp/upload0000"}), {
            "id": 1,
            "media_file_id": None,
            "state": "UploadedMediaFileState.PROCESSING",
        })

        process_uploaded_media_file.delay.assert_called_once_with(1)


class GetUploadTestCase(IntegrationTestCase):
    def prepare(self):
        uploaded_media_file = UploadedMediaFile()
        uploaded_media_file.state = UploadedMediaFileState.PROCESSING

        db.session.add(uploaded_media_file)
        db.session.commit()

    def test_get(self):
        self.assertEqual(self.get("/api/v1/media_files/uploads/1"), {
            "id": 1,
            "media_file_id": None,
            "state": "UploadedMediaFileState.PROCESSING",
        })
