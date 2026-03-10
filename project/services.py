"""
Translation Service Module

This module provides the core translation functionality for the TranslateIt application.
It handles language detection, translation, caching, and interaction with translation providers.
"""

import hashlib
import time
from typing import Dict, Optional, Tuple

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    TranslationNotFound,
)
from langdetect import LangDetectException, detect, detect_langs

from project.config import Configuration
from project.exceptions import (
    LanguageDetectionError,
    ProviderError,
    TextTooLongError,
    TranslationError,
    UnsupportedLanguageError,
)
from project.logger import get_logger


class TranslationService:
    """
    Service class for handling translation operations.

    This class provides methods for translating text, detecting languages,
    and managing a simple in-memory cache for translation results.
    """

    def __init__(self):
        """Initialize the translation service."""
        self.config = Configuration()
        self.logger = get_logger()
        self._cache: Dict[str, Tuple[str, float]] = {}
        self._supported_languages: Optional[Dict[str, str]] = None

        self.logger.info(
            f"TranslationService initialized with provider: {self.config.translation_provider}"
        )

    def _get_cache_key(self, text: str, source: str, target: str) -> str:
        """
        Generate a cache key for the given translation parameters.

        Args:
            text: Text to translate.
            source: Source language code.
            target: Target language code.

        Returns:
            str: Cache key hash.
        """
        key_string = f"{text}:{source}:{target}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Retrieve a translation from cache if it exists and hasn't expired.

        Args:
            cache_key: The cache key to look up.

        Returns:
            Optional[str]: Cached translation or None if not found/expired.
        """
        if not self.config.enable_cache:
            return None

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return result
            else:
                # Remove expired entry
                del self._cache[cache_key]
                self.logger.debug(f"Cache expired for key: {cache_key}")

        return None

    def _save_to_cache(self, cache_key: str, result: str) -> None:
        """
        Save a translation result to cache.

        Args:
            cache_key: The cache key.
            result: The translation result to cache.
        """
        if not self.config.enable_cache:
            return

        # Check cache size limit
        if len(self._cache) >= self.config.max_cache_size:
            # Remove oldest entry (simple FIFO eviction)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self.logger.debug(f"Cache full, evicted key: {oldest_key}")

        self._cache[cache_key] = (result, time.time())
        self.logger.debug(f"Saved to cache: {cache_key}")

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the given text.

        Args:
            text: Text to detect language from.

        Returns:
            Tuple[str, float]: Detected language code and confidence score.

        Raises:
            LanguageDetectionError: If language detection fails.
            TextTooLongError: If text exceeds maximum length.
        """
        if len(text) > self.config.max_text_length:
            self.logger.error(f"Text too long for detection: {len(text)} characters")
            raise TextTooLongError(max_length=self.config.max_text_length)

        if not self.config.enable_language_detection:
            self.logger.warning("Language detection is disabled in configuration")
            raise LanguageDetectionError("Language detection is disabled")

        try:
            self.logger.info(f"Detecting language for text: {text[:50]}...")
            detected_langs = detect_langs(text)

            if not detected_langs:
                raise LanguageDetectionError("Could not detect language")

            # Get the most probable language
            detected_lang = detected_langs[0]
            language_code = detected_lang.lang
            confidence = detected_lang.prob

            self.logger.info(
                f"Detected language: {language_code} with confidence: {confidence:.2f}"
            )
            return language_code, confidence

        except LangDetectException as e:
            self.logger.error(f"Language detection error: {str(e)}")
            raise LanguageDetectionError(f"Failed to detect language: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during language detection: {str(e)}")
            raise LanguageDetectionError(f"Unexpected error: {str(e)}")

    def translate(
            self, text: str, source_language: str = "auto", target_language: str = "en"
    ) -> Tuple[str, str]:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate.
            source_language: Source language code (use "auto" for detection).
            target_language: Target language code.

        Returns:
            Tuple[str, str]: Translated text and detected/specified source language.

        Raises:
            TextTooLongError: If text exceeds maximum length.
            UnsupportedLanguageError: If language pair is not supported.
            TranslationError: If translation fails.
        """
        # Validate text length
        if len(text) > self.config.max_text_length:
            self.logger.error(f"Text too long for translation: {len(text)} characters")
            raise TextTooLongError(max_length=self.config.max_text_length)

        # Handle auto-detection
        detected_source = source_language
        if source_language.lower() in ["auto", "none", ""]:
            self.logger.info("Auto-detecting source language")
            detected_source, confidence = self.detect_language(text)
            self.logger.info(
                f"Auto-detected source language: {detected_source} (confidence: {confidence:.2f})"
            )
        else:
            detected_source = source_language.lower()

        # Check if source and target are the same
        if detected_source == target_language.lower():
            self.logger.info("Source and target languages are the same, returning original text")
            return text, detected_source

        # Check cache
        cache_key = self._get_cache_key(text, detected_source, target_language)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self.logger.info("Returning cached translation")
            return cached_result, detected_source

        # Perform translation
        try:
            self.logger.info(
                f"Translating from {detected_source} to {target_language}: {text[:50]}..."
            )

            translator = GoogleTranslator(source=detected_source, target=target_language)
            translated_text = translator.translate(text)

            if not translated_text:
                raise TranslationError("Translation returned empty result")

            self.logger.info(f"Translation successful: {translated_text[:50]}...")

            # Save to cache
            self._save_to_cache(cache_key, translated_text)

            return translated_text, detected_source

        except LanguageNotSupportedException as e:
            self.logger.error(f"Unsupported language error: {str(e)}")
            raise UnsupportedLanguageError(f"Unsupported language pair: {str(e)}")
        except TranslationNotFound as e:
            self.logger.error(f"Translation not found: {str(e)}")
            raise TranslationError(f"Translation not found: {str(e)}")
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            raise ProviderError(f"Translation provider error: {str(e)}")

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get a dictionary of supported languages.

        Returns:
            Dict[str, str]: Dictionary mapping language codes to language names.
        """
        if self._supported_languages is not None:
            return self._supported_languages

        try:
            self.logger.info("Fetching supported languages")

            # Get supported languages from GoogleTranslator
            langs = GoogleTranslator().get_supported_languages(as_dict=True)

            self._supported_languages = langs
            self.logger.info(f"Found {len(langs)} supported languages")

            return langs

        except Exception as e:
            self.logger.error(f"Error fetching supported languages: {str(e)}")
            # Return a minimal set of common languages as fallback
            fallback_langs = {
                "en": "english",
                "es": "spanish",
                "fr": "french",
                "de": "german",
                "it": "italian",
                "pt": "portuguese",
                "ru": "russian",
                "zh-CN": "chinese (simplified)",
                "ja": "japanese",
                "ar": "arabic",
            }
            self.logger.warning(f"Using fallback language list: {len(fallback_langs)} languages")
            return fallback_langs

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self.logger.info("Clearing translation cache")
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict[str, int]: Cache statistics including size and max size.
        """
        return {
            "current_size": len(self._cache),
            "max_size": self.config.max_cache_size,
            "enabled": self.config.enable_cache,
        }
