# TranslateIt - FastAPI Translation Service

A production-ready multi-language translation service built with FastAPI, featuring automatic language detection, caching, comprehensive logging, and error handling.

## Features

- 🌍 **Multi-language Translation**: Support for 100+ languages via Google Translate
- 🔍 **Automatic Language Detection**: Detects source language automatically when not specified
- ⚡ **In-Memory Caching**: Configurable caching with TTL to reduce API calls
- 📝 **Comprehensive Logging**: Rotating file logs and console output
- 🛡️ **Global Error Handling**: Centralized exception handling with proper HTTP responses
- ⚙️ **Fully Configurable**: All settings managed via config.ini singleton pattern
- 🧪 **Well Tested**: Comprehensive test suite with pytest
- 📚 **Auto-Generated Docs**: Interactive API documentation with Swagger UI

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Hpro444/TranslateIT.git
cd TranslateIt
```

2. Create a virtual environment:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:

```bash
# For production
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt
```

## Configuration

On first run, a `config.ini` file will be created automatically in the project root with default values. You can modify this file to customize behavior:

```ini
[Server]
host = 0.0.0.0
port = 8000
debug_mode = False
reload = False

[Translation]
provider = google
timeout = 30
enable_cache = True
cache_ttl = 3600
max_text_length = 5000
max_cache_size = 1000

[Languages]
default_source = auto
default_target = en
enable_detection = True

[RateLimiting]
enabled = False
max_requests_per_minute = 60
max_concurrent_requests = 10

[Logging]
level = INFO
logs_dir = default
format = %%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s
enable_file_logging = True
max_bytes = 10485760
backup_count = 5

[APIKeys]
libre_api_url = https://libretranslate.com
libre_api_key =
yandex_api_key =
microsoft_api_key =
microsoft_region = 
```

## Environment Variables

Sensitive values such as translation API keys should live in a `.env` file rather than `config.ini`. Copy `.env.example` to `.env`, fill in the keys you actually need, and those values will automatically override the config file each time the application starts.

```ini
LIBRE_API_KEY =
YANDEX_API_KEY =
MICROSOFT_API_KEY =
MICROSOFT_REGION =
```

The repository already tracks `.env.example`, but you should **never** commit your real `.env` file. `python-dotenv` loads the variables before the rest of the configuration is applied.

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:8000` (or as configured).

### API Endpoints

#### 1. Translate Text

**POST** `/api/v1/translate`

```json
{
  "sentence": "Hello, how are you?",
  "source_language": "en",
  "target_language": "es"
}
```

Response:

```json
{
  "translated_text": "Hola, ¿cómo estás?",
  "detected_source_language": "en",
  "target_language": "es",
  "provider_used": "google"
}
```

For automatic language detection, set `source_language` to `"auto"` or omit it.

#### 2. Detect Language

**POST** `/api/v1/detect`

```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

Response:

```json
{
  "detected_language": "fr",
  "confidence": 0.95
}
```

#### 3. Get Supported Languages

**GET** `/api/v1/languages`

Response:

```json
{
  "languages": {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    ...
  },
  "count": 107
}
```

#### 4. Health Check

**GET** `/api/v1/health`

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Interactive API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=project

# Run specific test file
pytest tests/test_routes.py

# Run with verbose output
pytest -v
```

## Project Structure

```
TranslateIt/
├── project/                    # Main application package
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Configuration singleton
│   ├── models.py              # Pydantic models (DTOs)
│   ├── services.py            # Translation service logic
│   ├── routes.py              # API route definitions
│   ├── exceptions.py          # Custom exceptions
│   ├── error_handlers.py      # Global error handlers
│   └── logger.py              # Logging configuration
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_routes.py        # Route tests
│   └── test_services.py      # Service tests
├── logs/                      # Log files (created at runtime)
├── app.py                     # Application entry point
├── config.ini                 # Configuration file (created at runtime)
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
└── README.md                  # This file
```

## Development

### Code Formatting

```bash
# Format code with black
black .

# Sort imports
isort .

# Lint with flake8
flake8 project tests

# Type checking with mypy
mypy project
```

## Features in Detail

### Caching

- In-memory caching with configurable TTL (Time To Live)
- Cache size limits with FIFO eviction
- Can be enabled/disabled via configuration
- Reduces redundant API calls for repeated translations

### Logging

- Rotating file logs (configurable max size and backup count)
- Console output for real-time monitoring
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured log format with timestamps

### Error Handling

- Custom exception classes for different error types
- Global exception handlers for consistent error responses
- Proper HTTP status codes
- Detailed error messages for debugging

### Language Detection

- Automatic detection using langdetect library
- Confidence scores for detection accuracy
- Fallback to default language if detection fails
- Can be disabled via configuration

## Dependencies

### Core

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation using Python type annotations
- **deep-translator**: Translation library supporting multiple providers
- **langdetect**: Language detection library

### Development

- **pytest**: Testing framework
- **pytest-asyncio**: Async support for pytest
- **httpx**: HTTP client for testing
- **black**: Code formatter
- **flake8**: Code linter
- **mypy**: Static type checker
- **isort**: Import sorter
