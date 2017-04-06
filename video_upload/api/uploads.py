# -*- coding=utf-8 -*-
from flask_restplus import fields, Resource
import logging

from video_upload.app import api
from video_upload.db import db
from video_upload.models import UploadedMediaFile, UploadedMediaFileState
from video_upload.worker.ffmpeg import process_uploaded_media_file

logger = logging.getLogger(__name__)

ns = api.namespace("media_files/uploads", description="Uploading media files and retrieving their convertation status")
api.add_namespace(ns)

upload_model = api.model("Uploaded media file", {
    "id": fields.Integer(readonly=True, description="Unique identifier"),
    "state": fields.String(readonly=True, description="Upload state", enum=UploadedMediaFileState),
    "media_file_id": fields.Integer(readonly=True, description="Processed media file ID", required=False),
})

upload_parser = api.parser()
upload_parser.add_argument("file.path", type=str, required=True)


@ns.route("/")
class UploadsResource(Resource):
    @ns.marshal_with(upload_model)
    def get(self):
        return db.session.query(UploadedMediaFile).order_by(UploadedMediaFile.id.desc()).all()


@ns.route("/upload")
class DoUploadResource(Resource):
    @ns.expect(upload_parser)
    @ns.marshal_with(upload_model)
    def post(self):
        args = upload_parser.parse_args()
        uploaded_media_file = UploadedMediaFile()
        uploaded_media_file.state = UploadedMediaFileState.PROCESSING
        uploaded_media_file.tmp_path = args["file.path"]
        db.session.add(uploaded_media_file)
        db.session.commit()

        process_uploaded_media_file.delay(uploaded_media_file.id)

        return uploaded_media_file


@ns.route("/<int:id>")
@ns.param("id", "ID")
@ns.response(404, "Uploaded media file not found")
class UploadResource(Resource):
    @ns.marshal_with(upload_model)
    def get(self, id):
        return db.session.query(UploadedMediaFile).filter(UploadedMediaFile.id == id).one()
