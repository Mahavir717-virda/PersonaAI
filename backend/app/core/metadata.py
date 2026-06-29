"""Application metadata used by settings and OpenAPI."""

APP_NAME = "PersonaAI"
VERSION = "1.0.0-alpha"
DESCRIPTION = (
    "Production backend foundation for the PersonaAI communication "
    "intelligence platform."
)
AUTHOR = "PersonaAI"
LICENSE = "MIT"

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Application and dependency health checks.",
    }
]
