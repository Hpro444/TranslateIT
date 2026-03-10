"""
Configuration Module

This module provides a singleton ``Configuration`` class for managing all
application configuration for the TranslateIt translation service.
It supports reading and writing settings from a ``config.ini`` file so that
all tuneable parameters can be persisted and overridden without touching source code.
"""

import configparser
import os
from typing import Optional

from dotenv import load_dotenv

_DEFAULT_SENTINEL = "default"


class Configuration:
    """
    Singleton class for managing application configuration.

    Loads settings from a ``config.ini`` file located at the project root.
    Provides sensible defaults for every setting and persists any changes back
    to disk via ``save()``.

    Sections in ``config.ini``:
        - ``[Server]``      – FastAPI server host, port, and debug mode.
        - ``[Translation]`` – Translation provider, timeout, cache settings.
        - ``[Languages]``   – Default source and target languages.
        - ``[RateLimiting]``– Rate limiting and request constraints.
        - ``[Logging]``     – Logging configuration.
        - ``[APIKeys]``     – API keys for various providers.

    Usage::

        config = Configuration()
        print(config.translation_provider)
    """

    _instance: Optional["Configuration"] = None
    _initialized: bool = False

    def __new__(cls) -> "Configuration":
        """Create or return the existing singleton instance."""
        if cls._instance is None:
            cls._instance = super(Configuration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Initialise the Configuration singleton.

        On first call the constructor resolves all directory paths relative to
        the project root, sets default values for every setting, reads any
        existing ``config.ini`` to override those defaults, and then writes the
        (potentially merged) configuration back to disk.

        Subsequent calls are no-ops because ``_initialized`` is ``True``.
        """
        if self._initialized:
            return

        self._initialized = True

        config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.root = config_dir
        self._filepath = os.path.join(config_dir, "config.ini")

        # Load environment variables from .env before reading the config file
        load_dotenv(os.path.join(config_dir, ".env"))

        # Compute default paths
        self._default_logs_dir = os.path.join(config_dir, "logs")
        self._default_cache_dir = os.path.join(config_dir, "cache")

        # Server defaults
        self._server_host: str = "0.0.0.0"
        self._server_port: int = 8000
        self._debug_mode: bool = False
        self._reload: bool = False

        # Translation defaults
        self._translation_provider: str = "google"  # google, mymemory, libre, yandex
        self._translation_timeout: int = 30
        self._enable_cache: bool = True
        self._cache_ttl: int = 3600
        self._max_text_length: int = 5000
        self._max_cache_size: int = 1000

        # Language defaults
        self._default_source_language: str = "auto"
        self._default_target_language: str = "en"
        self._enable_language_detection: bool = True

        # Rate limiting defaults
        self._enable_rate_limiting: bool = False
        self._max_requests_per_minute: int = 60
        self._max_concurrent_requests: int = 10

        # Logging defaults
        self._log_level: str = "INFO"
        self._logs_dir: str = self._default_logs_dir
        self._log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self._enable_file_logging: bool = True
        self._log_max_bytes: int = 10485760  # 10MB
        self._log_backup_count: int = 5

        # LibreTranslate specific (if used)
        self._libre_api_url: str = "https://libretranslate.com"
        self._libre_api_key: str = ""

        # Yandex specific (if used)
        self._yandex_api_key: str = ""

        # Microsoft specific (if used)
        self._microsoft_api_key: str = ""
        self._microsoft_region: str = ""

        self._config_parser = configparser.ConfigParser()

        self.load()

    @staticmethod
    def _path_to_ini(path: str, default: str) -> str:
        """Return ``"default"`` when *path* equals *default*, else *path*."""
        return _DEFAULT_SENTINEL if path == default else path

    @staticmethod
    def _path_from_ini(value: str, default: str) -> str:
        """Return *default* when *value* is ``"default"`` (case-insensitive), else *value*."""
        return default if value.strip().lower() == _DEFAULT_SENTINEL else value

    def _override_with_env(self) -> None:
        """Override API key settings with values from the .env file or environment."""
        self._libre_api_url = os.getenv("LIBRE_API_URL", self._libre_api_url)
        self._libre_api_key = os.getenv("LIBRE_API_KEY", self._libre_api_key)
        self._yandex_api_key = os.getenv("YANDEX_API_KEY", self._yandex_api_key)
        self._microsoft_api_key = os.getenv("MICROSOFT_API_KEY", self._microsoft_api_key)
        self._microsoft_region = os.getenv("MICROSOFT_REGION", self._microsoft_region)

    def _value_for_save(self, env_var: str, value: str) -> str:
        """Return a portable placeholder when a value is coming from the environment."""
        env_value = os.getenv(env_var)
        if env_value:
            return _DEFAULT_SENTINEL
        return value

    def load(self) -> None:
        """
        Load configuration from the ``config.ini`` file.

        If the file does not yet exist, defaults are kept and ``save()`` is
        called to create it for the first time.
        """
        if os.path.exists(self._filepath):
            self._config_parser.read(self._filepath)

            # Server section
            self._server_host = self._config_parser.get(
                "Server", "host", fallback=self._server_host
            )
            self._server_port = self._config_parser.getint(
                "Server", "port", fallback=self._server_port
            )
            self._debug_mode = self._config_parser.getboolean(
                "Server", "debug_mode", fallback=self._debug_mode
            )
            self._reload = self._config_parser.getboolean(
                "Server", "reload", fallback=self._reload
            )

            # Translation section
            self._translation_provider = self._config_parser.get(
                "Translation", "provider", fallback=self._translation_provider
            )
            self._translation_timeout = self._config_parser.getint(
                "Translation", "timeout", fallback=self._translation_timeout
            )
            self._enable_cache = self._config_parser.getboolean(
                "Translation", "enable_cache", fallback=self._enable_cache
            )
            self._cache_ttl = self._config_parser.getint(
                "Translation", "cache_ttl", fallback=self._cache_ttl
            )
            self._max_text_length = self._config_parser.getint(
                "Translation", "max_text_length", fallback=self._max_text_length
            )
            self._max_cache_size = self._config_parser.getint(
                "Translation", "max_cache_size", fallback=self._max_cache_size
            )

            # Languages section
            self._default_source_language = self._config_parser.get(
                "Languages", "default_source", fallback=self._default_source_language
            )
            self._default_target_language = self._config_parser.get(
                "Languages", "default_target", fallback=self._default_target_language
            )
            self._enable_language_detection = self._config_parser.getboolean(
                "Languages",
                "enable_detection",
                fallback=self._enable_language_detection,
            )

            # Rate limiting section
            self._enable_rate_limiting = self._config_parser.getboolean(
                "RateLimiting", "enabled", fallback=self._enable_rate_limiting
            )
            self._max_requests_per_minute = self._config_parser.getint(
                "RateLimiting",
                "max_requests_per_minute",
                fallback=self._max_requests_per_minute,
            )
            self._max_concurrent_requests = self._config_parser.getint(
                "RateLimiting",
                "max_concurrent_requests",
                fallback=self._max_concurrent_requests,
            )

            # Logging section
            self._log_level = self._config_parser.get(
                "Logging", "level", fallback=self._log_level
            )
            self._logs_dir = self._path_from_ini(
                self._config_parser.get("Logging", "logs_dir", fallback=_DEFAULT_SENTINEL),
                self._default_logs_dir,
            )
            self._log_format = self._config_parser.get(
                "Logging", "format", fallback=self._log_format, raw=True
            )
            self._enable_file_logging = self._config_parser.getboolean(
                "Logging", "enable_file_logging", fallback=self._enable_file_logging
            )
            self._log_max_bytes = self._config_parser.getint(
                "Logging", "max_bytes", fallback=self._log_max_bytes
            )
            self._log_backup_count = self._config_parser.getint(
                "Logging", "backup_count", fallback=self._log_backup_count
            )

            # API Keys section
            self._libre_api_url = self._config_parser.get(
                "APIKeys", "libre_api_url", fallback=self._libre_api_url
            )
            self._libre_api_key = self._config_parser.get(
                "APIKeys", "libre_api_key", fallback=self._libre_api_key
            )
            self._yandex_api_key = self._config_parser.get(
                "APIKeys", "yandex_api_key", fallback=self._yandex_api_key
            )
            self._microsoft_api_key = self._config_parser.get(
                "APIKeys", "microsoft_api_key", fallback=self._microsoft_api_key
            )
            self._microsoft_region = self._config_parser.get(
                "APIKeys", "microsoft_region", fallback=self._microsoft_region
            )

        self._override_with_env()
        self.save()

    def save(self) -> None:
        """
        Save the current configuration to ``config.ini``.

        Creates the file (and any missing parent directories) if they do not
        already exist.
        """
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)

        self._config_parser["Server"] = {
            "host": self._server_host,
            "port": str(self._server_port),
            "debug_mode": str(self._debug_mode),
            "reload": str(self._reload),
        }

        self._config_parser["Translation"] = {
            "provider": self._translation_provider,
            "timeout": str(self._translation_timeout),
            "enable_cache": str(self._enable_cache),
            "cache_ttl": str(self._cache_ttl),
            "max_text_length": str(self._max_text_length),
            "max_cache_size": str(self._max_cache_size),
        }

        self._config_parser["Languages"] = {
            "default_source": self._default_source_language,
            "default_target": self._default_target_language,
            "enable_detection": str(self._enable_language_detection),
        }

        self._config_parser["RateLimiting"] = {
            "enabled": str(self._enable_rate_limiting),
            "max_requests_per_minute": str(self._max_requests_per_minute),
            "max_concurrent_requests": str(self._max_concurrent_requests),
        }

        self._config_parser["Logging"] = {
            "level": self._log_level,
            "logs_dir": self._path_to_ini(self._logs_dir, self._default_logs_dir),
            "format": self._log_format,
            "enable_file_logging": str(self._enable_file_logging),
            "max_bytes": str(self._log_max_bytes),
            "backup_count": str(self._log_backup_count),
        }

        self._config_parser["APIKeys"] = {
            "libre_api_url": self._libre_api_url,
            "libre_api_key": self._value_for_save("LIBRE_API_KEY", self._libre_api_key),
            "yandex_api_key": self._value_for_save("YANDEX_API_KEY", self._yandex_api_key),
            "microsoft_api_key": self._value_for_save("MICROSOFT_API_KEY", self._microsoft_api_key),
            "microsoft_region": self._value_for_save("MICROSOFT_REGION", self._microsoft_region),
        }

        with open(self._filepath, "w", encoding="utf-8") as configfile:
            self._config_parser.write(configfile)

    # Server properties
    @property
    def server_host(self) -> str:
        """Return the server host address."""
        return self._server_host

    @server_host.setter
    def server_host(self, value: str) -> None:
        """Set the server host address."""
        self._server_host = value

    @property
    def server_port(self) -> int:
        """Return the server port."""
        return self._server_port

    @server_port.setter
    def server_port(self, value: int) -> None:
        """Set the server port."""
        self._server_port = value

    @property
    def debug_mode(self) -> bool:
        """Return whether debug mode is enabled."""
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool) -> None:
        """Set whether debug mode is enabled."""
        self._debug_mode = value

    @property
    def reload(self) -> bool:
        """Return whether auto-reload is enabled."""
        return self._reload

    @reload.setter
    def reload(self, value: bool) -> None:
        """Set whether auto-reload is enabled."""
        self._reload = value

    # Translation properties
    @property
    def translation_provider(self) -> str:
        """Return the translation provider (google, mymemory, libre, yandex, microsoft)."""
        return self._translation_provider

    @translation_provider.setter
    def translation_provider(self, value: str) -> None:
        """Set the translation provider."""
        self._translation_provider = value

    @property
    def translation_timeout(self) -> int:
        """Return the translation request timeout in seconds."""
        return self._translation_timeout

    @translation_timeout.setter
    def translation_timeout(self, value: int) -> None:
        """Set the translation request timeout in seconds."""
        self._translation_timeout = value

    @property
    def enable_cache(self) -> bool:
        """Return whether caching is enabled."""
        return self._enable_cache

    @enable_cache.setter
    def enable_cache(self, value: bool) -> None:
        """Set whether caching is enabled."""
        self._enable_cache = value

    @property
    def cache_ttl(self) -> int:
        """Return the cache TTL in seconds."""
        return self._cache_ttl

    @cache_ttl.setter
    def cache_ttl(self, value: int) -> None:
        """Set the cache TTL in seconds."""
        self._cache_ttl = value

    @property
    def max_text_length(self) -> int:
        """Return the maximum allowed text length for translation."""
        return self._max_text_length

    @max_text_length.setter
    def max_text_length(self, value: int) -> None:
        """Set the maximum allowed text length for translation."""
        self._max_text_length = value

    @property
    def max_cache_size(self) -> int:
        """Return the maximum cache size."""
        return self._max_cache_size

    @max_cache_size.setter
    def max_cache_size(self, value: int) -> None:
        """Set the maximum cache size."""
        self._max_cache_size = value

    # Language properties
    @property
    def default_source_language(self) -> str:
        """Return the default source language."""
        return self._default_source_language

    @default_source_language.setter
    def default_source_language(self, value: str) -> None:
        """Set the default source language."""
        self._default_source_language = value

    @property
    def default_target_language(self) -> str:
        """Return the default target language."""
        return self._default_target_language

    @default_target_language.setter
    def default_target_language(self, value: str) -> None:
        """Set the default target language."""
        self._default_target_language = value

    @property
    def enable_language_detection(self) -> bool:
        """Return whether automatic language detection is enabled."""
        return self._enable_language_detection

    @enable_language_detection.setter
    def enable_language_detection(self, value: bool) -> None:
        """Set whether automatic language detection is enabled."""
        self._enable_language_detection = value

    # Rate limiting properties
    @property
    def enable_rate_limiting(self) -> bool:
        """Return whether rate limiting is enabled."""
        return self._enable_rate_limiting

    @enable_rate_limiting.setter
    def enable_rate_limiting(self, value: bool) -> None:
        """Set whether rate limiting is enabled."""
        self._enable_rate_limiting = value

    @property
    def max_requests_per_minute(self) -> int:
        """Return the maximum requests per minute."""
        return self._max_requests_per_minute

    @max_requests_per_minute.setter
    def max_requests_per_minute(self, value: int) -> None:
        """Set the maximum requests per minute."""
        self._max_requests_per_minute = value

    @property
    def max_concurrent_requests(self) -> int:
        """Return the maximum concurrent requests."""
        return self._max_concurrent_requests

    @max_concurrent_requests.setter
    def max_concurrent_requests(self, value: int) -> None:
        """Set the maximum concurrent requests."""
        self._max_concurrent_requests = value

    # Logging properties
    @property
    def log_level(self) -> str:
        """Return the logging level."""
        return self._log_level

    @log_level.setter
    def log_level(self, value: str) -> None:
        """Set the logging level."""
        self._log_level = value

    @property
    def logs_dir(self) -> str:
        """Return the logs directory."""
        return self._logs_dir

    @logs_dir.setter
    def logs_dir(self, value: str) -> None:
        """Set the logs directory."""
        self._logs_dir = value

    @property
    def log_format(self) -> str:
        """Return the log format string."""
        return self._log_format

    @log_format.setter
    def log_format(self, value: str) -> None:
        """Set the log format string."""
        self._log_format = value

    @property
    def enable_file_logging(self) -> bool:
        """Return whether file logging is enabled."""
        return self._enable_file_logging

    @enable_file_logging.setter
    def enable_file_logging(self, value: bool) -> None:
        """Set whether file logging is enabled."""
        self._enable_file_logging = value

    @property
    def log_max_bytes(self) -> int:
        """Return the maximum log file size in bytes."""
        return self._log_max_bytes

    @log_max_bytes.setter
    def log_max_bytes(self, value: int) -> None:
        """Set the maximum log file size in bytes."""
        self._log_max_bytes = value

    @property
    def log_backup_count(self) -> int:
        """Return the number of backup log files to keep."""
        return self._log_backup_count

    @log_backup_count.setter
    def log_backup_count(self, value: int) -> None:
        """Set the number of backup log files to keep."""
        self._log_backup_count = value

    # API Keys properties
    @property
    def libre_api_url(self) -> str:
        """Return the LibreTranslate API URL."""
        return self._libre_api_url

    @libre_api_url.setter
    def libre_api_url(self, value: str) -> None:
        """Set the LibreTranslate API URL."""
        self._libre_api_url = value

    @property
    def libre_api_key(self) -> str:
        """Return the LibreTranslate API key."""
        return self._libre_api_key

    @libre_api_key.setter
    def libre_api_key(self, value: str) -> None:
        """Set the LibreTranslate API key."""
        self._libre_api_key = value

    @property
    def yandex_api_key(self) -> str:
        """Return the Yandex API key."""
        return self._yandex_api_key

    @yandex_api_key.setter
    def yandex_api_key(self, value: str) -> None:
        """Set the Yandex API key."""
        self._yandex_api_key = value

    @property
    def microsoft_api_key(self) -> str:
        """Return the Microsoft Translator API key."""
        return self._microsoft_api_key

    @microsoft_api_key.setter
    def microsoft_api_key(self, value: str) -> None:
        """Set the Microsoft Translator API key."""
        self._microsoft_api_key = value

    @property
    def microsoft_region(self) -> str:
        """Return the Microsoft Translator region."""
        return self._microsoft_region

    @microsoft_region.setter
    def microsoft_region(self, value: str) -> None:
        """Set the Microsoft Translator region."""
        self._microsoft_region = value
