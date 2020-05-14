# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the base functionality all configs should have."""

from typing import Type, TypeVar

import rapidjson as json
from pydantic import BaseModel

from ._types import SemanticSpec, SemanticVersion

Config_T = TypeVar("Config_T")


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

        json_encoders = {SemanticSpec: str, SemanticVersion: str}
        json_loads = json.loads
        json_dumps = json.dumps

    @classmethod
    def from_json(cls: Type[Config_T], json_content: str) -> Config_T:
        """Load a new instance of the config from a JSON string.

        :return: The JSON string to load the config instance from
        :rtype: Config_T
        """

        return cls(**json.loads(json_content))  # type: ignore

    def to_json(self, *args, **kwargs) -> str:
        """Dump the config instance to a JSON string.

        :return: The JSON representation of the config instance
        :rtype: str
        """

        return self.json(*args, **kwargs)
