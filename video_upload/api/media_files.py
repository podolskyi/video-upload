# -*- coding=utf-8 -*-
from flask import redirect, request
from flask_restplus import abort, fields, Resource
import logging
from sqlalchemy.orm.exc import NoResultFound

from video_upload.app import api, app
from video_upload.db import db
from video_upload.models import MediaFile, MediaFileVariant

logger = logging.getLogger(__name__)

ns = api.namespace("media_files", description="Processed media files")
api.add_namespace(ns)

media_file_model = api.model("Processed media file", {
    "id": fields.Integer(readonly=True, description="Unique identifier"),
    "variants": fields.Nested({
        variant_name: fields.Nested({
            "url": fields.String(readonly=True, description="Variant URL"),
        })
        for variant_name in app.config["MEDIA_FILE_VARIANTS"]
    }),
})


@ns.route("/<int:id>")
@ns.response(404, "Nedia file not found")
class MediaFileResource(Resource):
    @ns.marshal_with(media_file_model)
    def get(self, id):
        try:
            media_file = db.session.query(MediaFile).filter(MediaFile.id == id).one()
        except NoResultFound:
            raise abort(404)

        return {
            "id": media_file.id,
            "variants": {
                variant.variant_name: {
                    "url": api.url_for(MediaFileVariantResource, id=media_file.id, variant_name=variant.variant_name,
                                       _external=True),
                }
                for variant in media_file.variants
            }
        }


@ns.route("/<int:id>/variants/<variant_name>")
@ns.response(404, "Nedia file variant not found")
class MediaFileVariantResource(Resource):
    def get(self, id, variant_name):
        try:
            media_file = db.session.query(MediaFile).filter(MediaFile.id == id).one()
        except NoResultFound:
            raise abort(404)

        try:
            variant = (
                db.session.query(MediaFileVariant).
                    filter(MediaFileVariant.media_file == media_file,
                           MediaFileVariant.variant_name == variant_name).
                    one()
            )
        except NoResultFound:
            raise abort(404)

        return redirect("/media/%s" % variant.blob.name)
