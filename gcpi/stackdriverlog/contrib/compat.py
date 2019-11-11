# -*- coding: utf-8 -*-
try:
    import django
    django_support = True
except ImportError:
    django_support = False

try:
    import flask
    flask_support = True
except ImportError:
    flask_support = False
