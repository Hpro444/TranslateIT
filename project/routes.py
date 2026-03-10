"""
Routes Module

This module defines all API endpoints for the TranslateIt application.
Routes are organized in a FastAPI APIRouter and handle translation,
language detection, supported languages, and health check endpoints.
"""

from fastapi import APIRouter, Depends

from project import __version__
from project.logger import get_logger
from project.models import (
    HealthResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    SupportedLanguagesResponse,
    TranslationRequest,
    TranslationResponse,
)
from project.services import TranslationService

logger = get_logger()

# Create API router
router = APIRouter()


def get_translation_service() -> TranslationService:
    """
    Dependency function to get TranslationService instance.

    Returns:
        TranslationService: A new or cached translation service instance.
    """
    return TranslationService()


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Translate text",
    description="Translate text from source language to target language. "
                "If source_language is 'auto' or not specified, the language will be automatically detected.",
)
async def translate(
        request: TranslationRequest,
        service: TranslationService = Depends(get_translation_service),
) -> TranslationResponse:
    """
    Translate text endpoint.

    Args:
        request: Translation request containing text and language parameters.
        service: Translation service instance (injected).

    Returns:
        TranslationResponse: Translation result with detected source language.
    """
    logger.info(
        f"Translation request: '{request.sentence[:50]}...' | "
        f"Source: {request.source_language} | Target: {request.target_language}"
    )

    translated_text, detected_source = service.translate(
        text=request.sentence,
        source_language=request.source_language or "auto",
        target_language=request.target_language,
    )

    logger.info(f"Translation completed successfully | Detected source: {detected_source}")

    return TranslationResponse(
        translated_text=translated_text,
        detected_source_language=detected_source,
        target_language=request.target_language,
        provider_used="google",
    )


@router.post(
    "/detect",
    response_model=LanguageDetectionResponse,
    summary="Detect language",
    description="Detect the language of the provided text with confidence score.",
)
async def detect_language(
        request: LanguageDetectionRequest,
        service: TranslationService = Depends(get_translation_service),
) -> LanguageDetectionResponse:
    """
    Language detection endpoint.

    Args:
        request: Language detection request containing text.
        service: Translation service instance (injected).

    Returns:
        LanguageDetectionResponse: Detected language and confidence score.
    """
    logger.info(f"Language detection request: '{request.text[:50]}...'")

    detected_language, confidence = service.detect_language(request.text)

    logger.info(
        f"Language detection completed | "
        f"Language: {detected_language} | Confidence: {confidence:.2f}"
    )

    return LanguageDetectionResponse(
        detected_language=detected_language,
        confidence=confidence,
    )


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="Get supported languages",
    description="Get a list of all supported languages with their codes and names.",
)
async def get_supported_languages(
        service: TranslationService = Depends(get_translation_service),
) -> SupportedLanguagesResponse:
    """
    Get supported languages endpoint.

    Args:
        service: Translation service instance (injected).

    Returns:
        SupportedLanguagesResponse: Dictionary of supported languages.
    """
    logger.info("Supported languages request")

    languages = service.get_supported_languages()

    logger.info(f"Returning {len(languages)} supported languages")

    return SupportedLanguagesResponse(
        languages=languages,
        count=len(languages),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the translation service.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service health status and version.
    """
    logger.debug("Health check request")

    return HealthResponse(
        status="healthy",
        version=__version__,
    )
