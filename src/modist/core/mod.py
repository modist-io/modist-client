# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the core mod modeling features."""

from pathlib import Path
from shutil import rmtree

import attr

from ..config.mod import ModConfig
from ..exceptions import IsAMod, NotAMod

MOD_DIRECTORY_NAME = ".mod"
MOD_DIRECTORY_MODE = 0o755
MOD_CONFIG_NAME = "mod.json"


@attr.s(repr=False)
class Mod:
    """Describes a locally available mod."""

    config: ModConfig = attr.ib(repr=False)
    path: Path = attr.ib()

    def __repr__(self) -> str:
        """Human readable representation of the Mod.

        :returns: A human readable representation of the Mod
        :rtype: str
        """

        return (
            f"{self.__class__.__qualname__!s}("
            f"name={self.config.name!s}, "
            f"version={self.config.version!s})"
        )

    @staticmethod
    def build_mod_directory_path(base_path: Path) -> Path:
        """Produce the mod directory path instance from the base directory path.

        :param Path base_path: The base directory path
        :return: The constructed mod directory path instance
        :rtype: Path
        """

        return base_path / MOD_DIRECTORY_NAME

    @staticmethod
    def build_mod_config_path(base_path: Path) -> Path:
        """Produce the mod config file path instance from the base directory path.

        :param Path base_path: The base directory path
        :return: The constructed mod config file path instance
        :rtype: Path
        """

        return Mod.build_mod_directory_path(base_path) / MOD_CONFIG_NAME

    @classmethod
    def create(
        cls,
        dirpath: Path,
        name: str,
        description: str,
        host: str,
        author: str,
        **kwargs,
    ) -> "Mod":
        """Initialize a new Mod instance for a specific base directory.

        :param str name: The name of the mod
        :param str description: The one-liner description of the mod
        :param str host: The host the mod is intended for
        :param str author: The author of the mod
        :raises NotADirectoryError: If the given base directory does not exist
        :raises IsAMod: If the given base directory already contains a mod
        :return: The newly created Mod instance
        :rtype: Mod
        """

        if not dirpath.is_dir():
            raise NotADirectoryError(f"No such directory {dirpath.as_posix()!r} exists")

        mod_dirpath = Mod.build_mod_directory_path(dirpath)
        if mod_dirpath.is_dir():
            raise IsAMod(
                f"Directory {dirpath.as_posix()!r} already contains a mod directory at "
                f"{mod_dirpath.as_posix()!r}"
            )
        mod_dirpath.mkdir(MOD_DIRECTORY_MODE, exist_ok=False)

        try:
            config: ModConfig = ModConfig(
                name=name, description=description, host=host, author=author, **kwargs
            )
            config_path = Mod.build_mod_config_path(dirpath)
            with config_path.open("w") as config_io:
                config_io.write(config.to_json(indent=2))

            return cls(config=config, path=dirpath)
        except Exception as exc:
            # Cleanup created mod directory if we fail creating the mod config file
            rmtree(mod_dirpath)
            raise exc

    @classmethod
    def from_dir(cls, dirpath: Path) -> "Mod":
        """Initialize a new Mod instance from a specific base directory.

        :raises NotADirectoryError: If the given base directory does not exist
        :raises NotAMod: If the given base directory contains no mod directory
        :raises NotAMod: If the given base directory contains no mod config file
        :return: The newly instantiated Mod instance
        :rtype: Mod
        """

        if not dirpath.is_dir():
            raise NotADirectoryError(f"No such directory {dirpath.as_posix()!r} exists")

        mod_dirpath = Mod.build_mod_directory_path(dirpath)
        if not mod_dirpath.is_dir():
            raise NotAMod(
                f"Directory {dirpath.as_posix()!r} has no mod directory at "
                f"{mod_dirpath.as_posix()!r}"
            )

        # Handle retroactively updating the mod directory mode if not using the required
        # directory permissions
        if mod_dirpath.stat().st_mode & ((1 << 12) - 1) != MOD_DIRECTORY_MODE:
            mod_dirpath.chmod(MOD_DIRECTORY_MODE)

        config_path = Mod.build_mod_config_path(dirpath)
        if not config_path.is_file():
            raise NotAMod(
                f"No {MOD_CONFIG_NAME!r} file found at {config_path.as_posix()!r}"
            )

        with config_path.open("r") as config_io:
            return cls(config=ModConfig.from_json(config_io.read()), path=dirpath)

    @property
    def mod_dirpath(self) -> Path:
        """Instance's mod directory path.

        :return: The mod instance's mod directory path
        :rtype: Path
        """

        return Mod.build_mod_directory_path(self.path)

    @property
    def mod_config_path(self) -> Path:
        """Instance's mod config path.

        :return: The mod instance's mod config path
        :rtype: Path
        """

        return Mod.build_mod_config_path(self.path)
