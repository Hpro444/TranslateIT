"""
Pytest configuration and fixtures for TranslateIt tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app import app
from project.services import TranslationService
from project.config import Configuration


@pytest.fixture
def test_client():
    """
    Fixture that provides a FastAPI TestClient.

    Returns:
        TestClient: FastAPI test client for making requests.
    """
    return TestClient(app)


@pytest.fixture
def mock_translation_service():
    """
    Fixture that provides a mocked TranslationService.

    Returns:
        Mock: Mocked TranslationService instance.
    """
    service = Mock(spec=TranslationService)

    # Setup default mock behaviors
    service.translate.return_value = ("Translated text", "en")
    service.detect_language.return_value = ("en", 0.95)
    service.get_supported_languages.return_value = {
        "en": "english",
        "es": "spanish",
        "fr": "french",
        "de": "german",
    }

    return service


@pytest.fixture
def sample_translation_request():
    """
    Fixture that provides sample translation request data.

    Returns:
        dict: Sample translation request.
    """
    return {
        "sentence": "Hello, how are you?",
        "source_language": "en",
        "target_language": "es",
    }


@pytest.fixture
def sample_detection_request():
    """
    Fixture that provides sample language detection request data.

    Returns:
        dict: Sample detection request.
    """
    return {
        "text": "Hello, this is a test sentence.",
    }


@pytest.fixture
def mock_google_translator():
    """
    Fixture that mocks the GoogleTranslator class.

    Returns:
        Mock: Mocked GoogleTranslator.
    """
    with patch("project.services.GoogleTranslator") as mock:
        translator_instance = Mock()
        translator_instance.translate.return_value = "Hola, ¿cómo estás?"
        translator_instance.get_supported_languages.return_value = {
            "en": "english",
            "es": "spanish",
            "fr": "french",
        }
        mock.return_value = translator_instance
        yield mock


@pytest.fixture
def mock_langdetect():
    """
    Fixture that mocks langdetect functions.

    Returns:
        Mock: Mocked langdetect.
    """
    with patch("project.services.detect_langs") as mock_detect_langs:
        mock_lang = Mock()
        mock_lang.lang = "en"
        mock_lang.prob = 0.95
        mock_detect_langs.return_value = [mock_lang]
        yield mock_detect_langs


@pytest.fixture(autouse=True)
def reset_configuration():
    config = Configuration()
    yield
    config.enable_language_detection = True
    config.enable_cache = True
    config.enable_rate_limiting = False
