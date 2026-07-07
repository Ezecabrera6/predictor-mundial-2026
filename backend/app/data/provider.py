"""Selección del proveedor de datos según configuración."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import settings
from ..models import Bracket


class DataProvider(ABC):
    @abstractmethod
    def get_bracket(self) -> Bracket:
        """Devuelve el cuadro (octavos→final) con equipos y sus factores."""


def get_provider() -> DataProvider:
    if settings.data_source == "api":
        from .worldcup26 import WorldCup26Provider

        return WorldCup26Provider()
    from .sample import SampleProvider

    return SampleProvider()
