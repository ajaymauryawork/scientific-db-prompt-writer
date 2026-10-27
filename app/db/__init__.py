from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class FieldDefinition:
    name: str
    type: str = "unknown"
    description: str = ""


@dataclass
class TableDefinition:
    name: str
    fields: List[FieldDefinition] = field(default_factory=list)


@dataclass
class DatabaseDefinition:
    name: str
    dialect: str = "unknown"
    tables: List[TableDefinition] = field(default_factory=list)


from .discovery import discover_database_metadata, guess_dialect  # noqa: E402

__all__ = [
    "FieldDefinition",
    "TableDefinition",
    "DatabaseDefinition",
    "guess_dialect",
    "discover_database_metadata",
]
