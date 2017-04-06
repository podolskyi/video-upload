import os

MEDIA_FILE_VARIANTS = {
    "720p": {
        "ext": "mp4",
        "content_type": "video/mp4",
        "ffmpeg_arguments": [
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "22",
            "-profile:v", "main",
            "-level", "4.0",
            "-pix_fmt", "yuv420p",
            "-c:a", "libmp3lame",
            "-b:a", "320k",
            "-filter:v", "scale='if(gt(a,16/9),iw*min(1,min(1280/iw,720/ih)),-1)':'if(gt(a,16/9),-1,ih*min(1,min(1280/iw,720/ih)))'",
            "-r", "25",
        ],
    },
    "360p": {
        "ext": "mp4",
        "content_type": "video/mp4",
        "ffmpeg_arguments": [
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "28",
            "-profile:v", "main",
            "-level", "4.0",
            "-pix_fmt", "yuv420p",
            "-c:a", "libmp3lame",
            "-b:a", "320k",
            "-filter:v", "scale='if(gt(a,16/9),iw*min(1,min(480/iw,360/ih)),-1)':'if(gt(a,16/9),-1,ih*min(1,min(480/iw,360/ih)))'",
            "-r", "25",
        ],
    },
}

MEDIA_FILES_PATH = "/www-root/media"

CELERY_BROKER_URL = "amqp://rabbitmq"
CELERYD_HIJACK_ROOT_LOGGER = False

SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@postgres/postgres"
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_ECHO = True

SENTRY_DSN = os.environ.get("SENTRY_DSN")
