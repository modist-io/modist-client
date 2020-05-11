# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

from pydantic import BaseModel, NameEmail

from ._types import SemanticSpec, SemanticVersion


class BaseConfig(BaseModel):
    """The base config model for all serializable config models.

    .. important:: This model provides the utilized ``json_encoders`` necessary to
        fully encode custom types for JSON representation. If you override the nested
        ``Config`` class in any config inheriting from ``BaseConfig``, you will need to
        redefine the appropriate ``json_encoders`` in that new ``Config`` definition.
    """

    class Config:
        """The base config's config.

        Contains the ``json_encoders`` necessary for all config JSON serialization.
        """

        json_encoders = {SemanticSpec: str, SemanticVersion: str, NameEmail: str}
