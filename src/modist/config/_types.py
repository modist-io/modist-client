# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom Pydantic types for use in configuration models."""

from typing import Callable, Generator

from semantic_version import SimpleSpec, Version, validate


class SemanticVersion(Version):
    """Custom :class:`semantic_version.Version` for pydantic field support.

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
        """Yield the necessary validator for the input string."""

        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        """Modify the pydantic build JSONSchema for this specified field.

        :param dict field_schema: The current field schema, pre-modification
        """

        field_schema.update(
            type="string",
            pattern=Version.version_re.pattern,
            examples=["1.0.0", "12.34.56-postrelease.1+build.891328232"],
        )

    @classmethod
    def validate(cls, value: str) -> Version:
        """Validate a given string and return an instance of the custom type.

        :param str value: The value to validate and use for instance building
        :raises TypeError: If the given value is not a string
        :raises ValueError: if the given value is not a valid Semver string
        :return: An instance of ``semantic_version.Version`` if validated
        :rtype: Version
        """

        if not isinstance(value, str):
            raise TypeError("string required")

        # NOTE: semantic-version provides it's own validate() method that returns a
        # boolean if the given value is a valid Semver string
        if not validate(value):
            raise ValueError(f"value {value!r} is not a valid SemVer string")

        return cls(value)


class SemanticSpec(SimpleSpec):
    """Custom :class:`semantic_version.SimpleSpec` for pydantic field support.

    Use this class just like a regular ol' pydantic field:
    >>> from ._types import SemanticSpec
    >>> class MyModel(BaseModel):
    ...     version_spec: SemanticSpec

    .. important:: If you intend to use this field for serialization back to JSON or to
        build JSON schemas with pydantic, you need to supply the encoder for this type
        **explicitly** in your model. 90% of the time you just need to use the
        ``__str__`` representation of the instance. If you need to get more complicated,
        create a short function to generate the string you need and use that in-place of
        the ``str`` callable in the following example:

        >>> class MyConfig(BaseModel)
        ...     class Config:
        ...         json_encoders = {SemanticSpec: str}
        ...
        ...     version_spec: SemanticSpec
    """

    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[str], "SemanticSpec"], None, None]:
        """Yield the necessary validator for the input string."""

        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        """Modify the pydnatic vuild JSONSchema for this specified field.

        :param dict field_schema: The current field schema, pre-modification
        """

        field_schema.update(type="string", examples=[">=0.1.0,<0.3.0", "1.2.3"])

    @classmethod
    def validate(cls, value: str) -> SimpleSpec:
        """Validate a given string and return an instance of the custom type.

        :param str value: The value to validate and use for instance building
        :raises TypeError: If the given value is not a string
        :return: An instance of ``semantic_version.SimpleSpec`` if validated
        :rtype: SimpleSpec
        """

        if not isinstance(value, str):
            raise TypeError("string required")

        return cls(value)
