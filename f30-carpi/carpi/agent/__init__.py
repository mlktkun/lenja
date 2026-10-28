"""KI-Agent (Claude) mit Werkzeugen für Telefon, Musik und Fahrzeug."""

from .claude_agent import CarAgent
from .tools import Toolbox

__all__ = ["CarAgent", "Toolbox"]
