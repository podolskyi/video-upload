# -*- coding=utf-8 -*-
import logging
from unittest.mock import Mock, patch

from video_upload.db import db
from video_upload.models import MediaFile, MediaFileVariant, Blob
from video_upload.utils.integration_test_case import IntegrationTestCase

logger = logging.getLogger(__name__)


class GetMediaFileTestCase(IntegrationTestCase):
    def prepare(self):
        media_file = MediaFile()
        media_file.probe = {"original": True}

        variant1 = MediaFileVariant()
        variant1.variant_name = "720p"
        variant1.media_file = media_file
        variant1.probe = {"mp4": True}
        variant1.blob = Blob()
        variant1.blob.name = "abc.mp4"

        variant2 = MediaFileVariant()
        variant2.variant_name = "360p"
        variant2.media_file = media_file
        variant2.probe = {"mp4": True}
        variant2.blob = Blob()
        variant2.blob.name = "def.mp4"

        db.session.add(media_file)
        db.session.commit()

    def test_get_media_file(self):
        self.assertEqual(
            self.get("/api/v1/media_files/1"),
            {
                "id": 1,
                "variants": {
                    "720p": {
                        "url": "http://localhost/api/v1/media_files/1/variants/720p",
                    },
                    "360p": {
                        "url": "http://localhost/api/v1/media_files/1/variants/360p",
                    },
                }
            }
        )

    def test_get_media_file_variant(self):
        response = self.get("/api/v1/media_files/1/variants/720p", _raw_response=True)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "http://localhost/media/abc.mp4")
