"""
Tests for TranslationService.
"""

import pytest
from unittest.mock import Mock, patch

from project.config import Configuration
from project.exceptions import (
    LanguageDetectionError,
    TextTooLongError,
    TranslationError,
    UnsupportedLanguageError,
    ProviderError,
)
from project.services import TranslationService


class TestTranslationService:
    """Tests for the TranslationService class."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = TranslationService()

        assert service is not None
        assert service.config is not None
        assert service.logger is not None
        assert isinstance(service._cache, dict)

    def test_cache_key_generation(self):
        """Test cache key generation."""
        service = TranslationService()

        key1 = service._get_cache_key("hello", "en", "es")
        key2 = service._get_cache_key("hello", "en", "es")
        key3 = service._get_cache_key("goodbye", "en", "es")

        assert key1 == key2
        assert key1 != key3

    def test_cache_operations(self):
        """Test cache save and retrieve operations."""
        service = TranslationService()
        service.config.enable_cache = True

        cache_key = service._get_cache_key("test", "en", "es")

        # Save to cache
        service._save_to_cache(cache_key, "prueba")

        # Retrieve from cache
        result = service._get_from_cache(cache_key)

        assert result == "prueba"

    def test_cache_disabled(self):
        """Test that cache doesn't save when disabled."""
        service = TranslationService()
        service.config.enable_cache = False

        cache_key = service._get_cache_key("test", "en", "es")

        # Try to save to cache
        service._save_to_cache(cache_key, "prueba")

        # Should not be in cache
        result = service._get_from_cache(cache_key)

        assert result is None

    def test_cache_expiration(self):
        """Test cache expiration based on TTL."""
        service = TranslationService()
        service.config.enable_cache = True
        service.config.cache_ttl = 0  # Expire immediately

        cache_key = service._get_cache_key("test", "en", "es")

        # Save to cache
        service._save_to_cache(cache_key, "prueba")

        # Should be expired
        import time
        time.sleep(0.1)
        result = service._get_from_cache(cache_key)

        assert result is None

    def test_detect_language_success(self, mock_langdetect):
        """Test successful language detection."""
        service = TranslationService()

        language, confidence = service.detect_language("Hello world")

        assert language == "en"
        assert 0.0 <= confidence <= 1.0

    def test_detect_language_text_too_long(self):
        """Test language detection with text exceeding max length."""
        service = TranslationService()

        long_text = "a" * (service.config.max_text_length + 1)

        with pytest.raises(TextTooLongError):
            service.detect_language(long_text)

    def test_detect_language_disabled(self):
        """Test language detection when disabled in config."""
        service = TranslationService()
        service.config.enable_language_detection = False

        with pytest.raises(LanguageDetectionError):
            service.detect_language("Hello world")

    def test_translate_success(self, mock_google_translator, mock_langdetect):
        """Test successful translation."""
        service = TranslationService()

        translated, source = service.translate("Hello", "en", "es")

        assert translated is not None
        assert source == "en"

    def test_translate_auto_detect(self, mock_google_translator, mock_langdetect):
        """Test translation with automatic language detection."""
        service = TranslationService()

        translated, source = service.translate("Hello world", "auto", "es")

        assert translated is not None
        assert source == "en"  # Should detect as English

    def test_translate_same_language(self, mock_google_translator, mock_langdetect):
        """Test translation when source and target are the same."""
        service = TranslationService()

        text = "Hello world"
        translated, source = service.translate(text, "en", "en")

        assert translated == text
        assert source == "en"

    def test_translate_text_too_long(self):
        """Test translation with text exceeding max length."""
        service = TranslationService()

        long_text = "a" * (service.config.max_text_length + 1)

        with pytest.raises(TextTooLongError):
            service.translate(long_text, "en", "es")

    def test_translate_with_cache_hit(self, mock_google_translator, mock_langdetect):
        """Test that cached translations are returned."""
        service = TranslationService()
        service.config.enable_cache = True

        # First call - should translate and cache
        translated1, _ = service.translate("Hello", "en", "es")

        # Second call - should return from cache
        translated2, _ = service.translate("Hello", "en", "es")

        assert translated1 == translated2

    def test_get_supported_languages(self, mock_google_translator):
        """Test getting supported languages."""
        service = TranslationService()

        languages = service.get_supported_languages()

        assert isinstance(languages, dict)
        assert len(languages) > 0

    def test_get_supported_languages_cached(self, mock_google_translator):
        """Test that supported languages are cached after first call."""
        service = TranslationService()

        # First call
        languages1 = service.get_supported_languages()

        # Second call - should return cached
        languages2 = service.get_supported_languages()

        assert languages1 is languages2

    def test_clear_cache(self):
        """Test cache clearing."""
        service = TranslationService()
        service.config.enable_cache = True

        # Add something to cache
        cache_key = service._get_cache_key("test", "en", "es")
        service._save_to_cache(cache_key, "prueba")

        assert len(service._cache) > 0

        # Clear cache
        service.clear_cache()

        assert len(service._cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        service = TranslationService()

        stats = service.get_cache_stats()

        assert "current_size" in stats
        assert "max_size" in stats
        assert "enabled" in stats
        assert isinstance(stats["current_size"], int)
        assert isinstance(stats["max_size"], int)
        assert isinstance(stats["enabled"], bool)

    def test_cache_size_limit(self):
        """Test that cache respects max size limit."""
        service = TranslationService()
        service.config.enable_cache = True
        service.config.max_cache_size = 3

        # Add more items than max size
        for i in range(5):
            cache_key = service._get_cache_key(f"test{i}", "en", "es")
            service._save_to_cache(cache_key, f"prueba{i}")

        # Cache size should not exceed max
        assert len(service._cache) <= service.config.max_cache_size


class TestTranslationServiceExceptions:
    """Tests for exception handling in TranslationService."""

    def test_unsupported_language_exception(self):
        """Test handling of unsupported language."""
        service = TranslationService()

        with patch("project.services.GoogleTranslator") as mock_translator:
            from deep_translator.exceptions import LanguageNotSupportedException

            mock_translator.return_value.translate.side_effect = LanguageNotSupportedException(
                "xx", "Unsupported"
            )

            with pytest.raises(UnsupportedLanguageError):
                service.translate("Hello", "en", "xx")

    def test_translation_provider_error(self):
        """Test handling of provider errors."""
        service = TranslationService()

        with patch("project.services.GoogleTranslator") as mock_translator:
            mock_translator.return_value.translate.side_effect = Exception("Network error")

            with pytest.raises(ProviderError):
                service.translate("Hello", "en", "es")

    def test_language_detection_exception(self):
        """Test handling of language detection errors."""
        service = TranslationService()

        with patch("project.services.detect_langs") as mock_detect:
            from langdetect import LangDetectException

            mock_detect.side_effect = LangDetectException("code", "message")

            with pytest.raises(LanguageDetectionError):
                service.detect_language("abc")
