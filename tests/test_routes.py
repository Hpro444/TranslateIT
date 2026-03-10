"""
Tests for API routes.
"""

import pytest
from unittest.mock import patch

from project.exceptions import (
    LanguageDetectionError,
    TextTooLongError,
    TranslationError,
    UnsupportedLanguageError,
)


class TestTranslateEndpoint:
    """Tests for the /api/v1/translate endpoint."""

    def test_translate_success(self, test_client, sample_translation_request, mock_google_translator):
        """Test successful translation."""
        with patch("project.services.detect_langs") as mock_detect:
            mock_lang = type("MockLang", (), {"lang": "en", "prob": 0.95})
            mock_detect.return_value = [mock_lang()]

            response = test_client.post("/api/v1/translate", json=sample_translation_request)

            assert response.status_code == 200
            data = response.json()
            assert "translated_text" in data
            assert "detected_source_language" in data
            assert "target_language" in data
            assert "provider_used" in data
            assert data["target_language"] == "es"

    def test_translate_auto_detect(self, test_client, mock_google_translator):
        """Test translation with automatic language detection."""
        with patch("project.services.detect_langs") as mock_detect:
            mock_lang = type("MockLang", (), {"lang": "en", "prob": 0.95})
            mock_detect.return_value = [mock_lang()]

            request_data = {
                "sentence": "Hello world",
                "source_language": "auto",
                "target_language": "es",
            }

            response = test_client.post("/api/v1/translate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["detected_source_language"] in ["en", "auto"]

    def test_translate_missing_target_language(self, test_client):
        """Test translation without target language (should fail validation)."""
        request_data = {
            "sentence": "Hello world",
            "source_language": "en",
        }

        response = test_client.post("/api/v1/translate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"] == "ValidationError"

    def test_translate_empty_sentence(self, test_client):
        """Test translation with empty sentence (should fail validation)."""
        request_data = {
            "sentence": "",
            "source_language": "en",
            "target_language": "es",
        }

        response = test_client.post("/api/v1/translate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_translate_text_too_long(self, test_client):
        """Test translation with text exceeding maximum length."""
        request_data = {
            "sentence": "a" * 10000,  # Exceeds default max length
            "source_language": "en",
            "target_language": "es",
        }

        response = test_client.post("/api/v1/translate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_translate_same_source_target(self, test_client, mock_google_translator):
        """Test translation when source and target languages are the same."""
        with patch("project.services.detect_langs") as mock_detect:
            mock_lang = type("MockLang", (), {"lang": "en", "prob": 0.95})
            mock_detect.return_value = [mock_lang()]

            request_data = {
                "sentence": "Hello world",
                "source_language": "en",
                "target_language": "en",
            }

            response = test_client.post("/api/v1/translate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            # Should return original text when source and target are the same
            assert data["translated_text"] == "Hello world"


class TestDetectEndpoint:
    """Tests for the /api/v1/detect endpoint."""

    def test_detect_language_success(self, test_client, sample_detection_request, mock_langdetect):
        """Test successful language detection."""
        response = test_client.post("/api/v1/detect", json=sample_detection_request)

        assert response.status_code == 200
        data = response.json()
        assert "detected_language" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_detect_empty_text(self, test_client):
        """Test language detection with empty text."""
        request_data = {"text": ""}

        response = test_client.post("/api/v1/detect", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_detect_text_too_long(self, test_client):
        """Test language detection with text exceeding maximum length."""
        request_data = {"text": "a" * 10000}

        response = test_client.post("/api/v1/detect", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "error" in data


class TestLanguagesEndpoint:
    """Tests for the /api/v1/languages endpoint."""

    def test_get_supported_languages(self, test_client, mock_google_translator):
        """Test getting supported languages."""
        response = test_client.get("/api/v1/languages")

        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert "count" in data
        assert isinstance(data["languages"], dict)
        assert data["count"] > 0
        assert data["count"] == len(data["languages"])


class TestHealthEndpoint:
    """Tests for the /api/v1/health endpoint."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, test_client):
        """Test 404 error for non-existent endpoint."""
        response = test_client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_405_method_not_allowed(self, test_client):
        """Test 405 error for wrong HTTP method."""
        response = test_client.get("/api/v1/translate")

        assert response.status_code == 405
        data = response.json()
        assert "error" in data
