"""
Data Models Module

This module defines Pydantic models (DTOs) for request and response schemas
used in the TranslateIt API.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

from project.config import Configuration


class TranslationRequest(BaseModel):
    """
    Request model for translation endpoint.

    Attributes:
        sentence: The text to translate.
        source_language: Source language code (default: "auto" for auto-detection).
        target_language: Target language code.
    """

    sentence: str = Field(..., description="Text to translate", min_length=1)
    source_language: Optional[str] = Field(
        default="auto",
        description="Source language code (use 'auto' for automatic detection)",
    )
    target_language: str = Field(..., description="Target language code", min_length=2)

    @field_validator("sentence")
    @classmethod
    def validate_sentence_length(cls, v: str) -> str:
        """
        Validate that the sentence doesn't exceed maximum length.

        Args:
            v: The sentence to validate.

        Returns:
            str: The validated sentence.

        Raises:
            ValueError: If sentence exceeds maximum length.
        """
        config = Configuration()
        if len(v) > config.max_text_length:
            raise ValueError(
                f"Text exceeds maximum length of {config.max_text_length} characters"
            )
        return v

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_code(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize language codes.

        Args:
            v: The language code to validate.

        Returns:
            Optional[str]: The normalized language code.
        """
        if v is None or v.lower() == "auto":
            return "auto"
        return v.lower()


class TranslationResponse(BaseModel):
    """
    Response model for translation endpoint.

    Attributes:
        translated_text: The translated text.
        detected_source_language: The detected or specified source language.
        target_language: The target language.
        provider_used: The translation provider used.
    """

    translated_text: str = Field(..., description="Translated text")
    detected_source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(..., description="Target language")
    provider_used: str = Field(..., description="Translation provider used")


class LanguageDetectionRequest(BaseModel):
    """
    Request model for language detection endpoint.

    Attributes:
        text: The text to detect language from.
    """

    text: str = Field(..., description="Text to detect language from", min_length=1)

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """
        Validate that the text doesn't exceed maximum length.

        Args:
            v: The text to validate.

        Returns:
            str: The validated text.

        Raises:
            ValueError: If text exceeds maximum length.
        """
        config = Configuration()
        if len(v) > config.max_text_length:
            raise ValueError(
                f"Text exceeds maximum length of {config.max_text_length} characters"
            )
        return v


class LanguageDetectionResponse(BaseModel):
    """
    Response model for language detection endpoint.

    Attributes:
        detected_language: The detected language code.
        confidence: Confidence score (0-1) of the detection.
    """

    detected_language: str = Field(..., description="Detected language code")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0.0, le=1.0)


class SupportedLanguagesResponse(BaseModel):
    """
    Response model for supported languages endpoint.

    Attributes:
        languages: Dictionary mapping language codes to language names.
        count: Total number of supported languages.
    """

    languages: Dict[str, str] = Field(..., description="Supported languages (code: name)")
    count: int = Field(..., description="Total number of supported languages")


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Attributes:
        status: Service health status.
        version: Application version.
    """

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
