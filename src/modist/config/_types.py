# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom Pydantic types for use in configuration models."""

import re
from typing import Callable, Generator

from semver import _REGEX, VersionInfo


class SemanticVersion(VersionInfo):
    """Custom subclass of ``semver.VersionInfo`` for pydantic field support.

    Use this class just like a regular ol' pydantic field:
    >>> from ._types import SemanticVersion
    >>> class MyModel(BaseModel):
    ...     version: SemanticVersion

    .. important:: If you intend to use this field for serialization back to JSON or to
        build JSON schemas with pydantic, you need to supply the encoder for this type
        **explicitly** in your model. 90% of the time you just need to use the
        ``__str__`` representation of the instance. If you need to get more complicated,
        create a short function to generate the string you need and use that in-place of
        the ``str`` callable in the following example:

        >>> class MyConfig(BaseModel)
        ...     class Config:
        ...         json_encoders = {SemanticVersion: str}
        ...
        ...     version: SemanticVersion
    """

    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[str], "SemanticVersion"], None, None]:
        """Yield the necessary validators for the input string."""

        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        """Modify the pydantic build JSONSchema for this specific field.

        :param dict field_schema: The current field schema, pre-modification
        """

        field_schema.update(
            type="string",
            pattern=re.sub(r"\s", "", _REGEX.pattern),
            examples=["1.0.0", "12.34.45-postrelease.1+build.891328232"],
        )

    @classmethod
    def validate(cls, value: str) -> VersionInfo:
        """Validate a given string and return an instance of the custom type.

        :param str value: The value to validate and use for instance building
        :raises TypeError: If the given value is not a string
        :return: An instance of ``semver.VersionInfo`` if validated
        :rtype: VersionInfo
        """

        if not isinstance(value, str):
            raise TypeError("string required")

        return cls.parse(value)
