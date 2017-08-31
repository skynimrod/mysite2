# -*-  coding: utf-8  -*-

from __future__ import absolute_import

import pymysql
pymysql.install_as_MySQLdb()

# This will make sure the app is always imported when
# Django starts so that share_task will use this app.
from .celery import app as celery_app


