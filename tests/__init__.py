# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains unit tests for the module."""

import os
import sys

from hypothesis import HealthCheck, settings

from modist.log.client import configure_logger

configure_logger({"handlers": [{"sink": os.devnull, "level": "CRITICAL"}]})

settings.register_profile("default", max_examples=30)
settings.register_profile(
    "ci", suppress_health_check=[HealthCheck.too_slow], max_examples=30, deadline=None
)
settings.register_profile(
    "windows",
    suppress_health_check=[HealthCheck.too_slow],
    max_examples=10,
    deadline=None,
)

settings.load_profile("default")

if sys.platform in ("win32",):
    settings.load_profile("windows")

if os.environ.get("CI", None) == "true":
    settings.load_profile("ci")
