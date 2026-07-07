"""Proveedor de datos de ejemplo (lee sample_data.json). No requiere internet."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Bracket
from .provider import DataProvider

_DATA_FILE = Path(__file__).parent / "sample_data.json"


class SampleProvider(DataProvider):
    def get_bracket(self) -> Bracket:
        with _DATA_FILE.open(encoding="utf-8") as f:
            raw = json.load(f)
        return Bracket.model_validate(raw)
