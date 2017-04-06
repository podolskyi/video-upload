# -*- coding=utf-8 -*-
import json
import logging
import unittest
import urllib.parse

from video_upload import app
from video_upload.db import db
from video_upload.models import *

logger = logging.getLogger(__name__)


class IntegrationTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.e = {}
        for i in range(400, 599):
            self.e[i] = type("Error%d" % i, (Exception,), {})

    def setUp(self):
        db.session.remove()

        db.drop_all()
        db.create_all()

        self.app = app.test_client()

        self.prepare()

    def prepare(self):
        pass

    def refresh_db(self):
        for o in db.session:
            db.session.refresh(o)

    def get(self, url, data=None, **kwargs):
        return self.request("get", url + ("?%s" % urllib.parse.urlencode(data) if data else ""), **kwargs)

    def patch(self, url, data, **kwargs):
        return self.request("patch", url, data=json.dumps(data), **kwargs)

    def post(self, url, data, **kwargs):
        return self.request("post", url, data=data, **kwargs)

    def put(self, url, data, **kwargs):
        return self.request("put", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("delete", url, **kwargs)

    def request(self, method, url, **kwargs):
        _raw_response = kwargs.pop("_raw_response", False)

        meth = getattr(self.app, method)
        response = meth(url, **kwargs)
        try:
            if _raw_response:
                return response

            if response.status_code >= 400:
                raise self.e[response.status_code](response.data)
            if response.status_code == 204:
                return None
            return json.loads(response.data.decode("ascii"))
        finally:
            self.refresh_db()

    def assertIncludes(self, a, b):
        for k, v in b.items():
            self.assertEqual(a[k], v, "for key %r" % k)
