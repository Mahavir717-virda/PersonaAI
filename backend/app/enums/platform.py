"""Communication platform enums."""

from enum import StrEnum


class Platform(StrEnum):
    """Supported communication source platforms."""

    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_DRIVE = "google_drive"
    MICROSOFT_TEAMS = "microsoft_teams"
    ZOOM = "zoom"
