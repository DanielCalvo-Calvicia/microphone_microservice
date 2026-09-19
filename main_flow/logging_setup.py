import logging

_ALIASES = {"TRACE": "DEBUG", "WARN": "WARNING"}


def configure_logging(level_name: str) -> None:
    """Configure root logging; unknown names fall back to INFO."""
    name = level_name.upper()
    level = getattr(logging, _ALIASES.get(name, name), logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
