from flask import Blueprint, Flask
from flask_restplus import Api
import logging

import video_upload.config

logger = logging.getLogger(__name__)

__all__ = ["api", "app"]

app = Flask("video_upload")
app.config.from_object(video_upload.config)
app.url_map.strict_slashes = False

api_v1 = Blueprint("video_upload", __name__, url_prefix="/api/v1")
api = Api(api_v1)
app.register_blueprint(api_v1)
