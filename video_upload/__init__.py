import codecs
import logging
from raven.contrib.flask import Sentry
import sys
from werkzeug.exceptions import HTTPException

from video_upload.app import app
from video_upload.celery import celery
from video_upload.db import db
from video_upload.models import *

import video_upload.api
import video_upload.worker

logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
                    stream=codecs.getwriter("utf-8")(sys.stdout.buffer, "replace") if hasattr(sys.stdout, "buffer") else None)
logging.getLogger("amqp").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.INFO)
logging.getLogger("celery.redirected").setLevel(logging.ERROR)
logging.getLogger("kombu").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

if app.config.get("SENTRY_DSN"):
    app.config["RAVEN_IGNORE_EXCEPTIONS"] = [HTTPException]
    sentry = Sentry(app)
