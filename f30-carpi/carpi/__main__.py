"""Startet den Bordcomputer: `python -m carpi` (Einstellungen über CARPI_*-Variablen)."""

from __future__ import annotations

import logging

import uvicorn

from .config import Settings
from .server import build_services, create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings()
    app = create_app(build_services(settings))
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
