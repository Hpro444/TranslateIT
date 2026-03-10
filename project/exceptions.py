"""
Custom Exceptions Module

This module defines custom exceptions for the TranslateIt application.
All custom exceptions inherit from the base TranslateItException class.
"""


class TranslateItException(Exception):
    """Base exception class for all TranslateIt exceptions."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize the exception.

        Args:
            message: Error message describing what went wrong.
            status_code: HTTP status code to return (default: 500).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TranslationError(TranslateItException):
    """Exception raised when translation fails."""

    def __init__(self, message: str = "Translation failed"):
        """
        Initialize translation error.

        Args:
            message: Error message (default: "Translation failed").
        """
        super().__init__(message, status_code=500)


class LanguageDetectionError(TranslateItException):
    """Exception raised when language detection fails."""

    def __init__(self, message: str = "Language detection failed"):
        """
        Initialize language detection error.

        Args:
            message: Error message (default: "Language detection failed").
        """
        super().__init__(message, status_code=500)


class UnsupportedLanguageError(TranslateItException):
    """Exception raised when an unsupported language is requested."""

    def __init__(self, message: str = "Unsupported language"):
        """
        Initialize unsupported language error.

        Args:
            message: Error message (default: "Unsupported language").
        """
        super().__init__(message, status_code=400)


class TextTooLongError(TranslateItException):
    """Exception raised when text exceeds maximum length."""

    def __init__(self, message: str = "Text exceeds maximum length", max_length: int = 5000):
        """
        Initialize text too long error.

        Args:
            message: Error message (default: "Text exceeds maximum length").
            max_length: The maximum allowed length.
        """
        full_message = f"{message}. Maximum allowed length: {max_length} characters."
        super().__init__(full_message, status_code=400)


class ProviderError(TranslateItException):
    """Exception raised when translation provider encounters an error."""

    def __init__(self, message: str = "Translation provider error"):
        """
        Initialize provider error.

        Args:
            message: Error message (default: "Translation provider error").
        """
        super().__init__(message, status_code=503)


class ConfigurationError(TranslateItException):
    """Exception raised when there's a configuration issue."""

    def __init__(self, message: str = "Configuration error"):
        """
        Initialize configuration error.

        Args:
            message: Error message (default: "Configuration error").
        """
        super().__init__(message, status_code=500)
