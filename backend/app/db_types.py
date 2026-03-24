"""
Database-agnostic column types for SQLite (and any DB without native pgvector/UUID).

PortableUUID  — Stores UUID as VARCHAR(36) string (with dashes).
                Accepts str, uuid.UUID, or anything str()-able as input.
                Always returns uuid.UUID Python objects on read.

EmbeddingType — Stores a list[float] as a JSON text blob.
                Reads it back as list[float].
"""
import uuid
import json
from sqlalchemy.types import TypeDecorator, String, Text


class PortableUUID(TypeDecorator):
    """Cross-database UUID stored as VARCHAR(36). No native UUID required."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Accept uuid.UUID objects, hyphenated strings, or plain hex strings
        if isinstance(value, uuid.UUID):
            return str(value)
        try:
            return str(uuid.UUID(str(value)))
        except (ValueError, AttributeError):
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return value


class EmbeddingType(TypeDecorator):
    """Stores a list[float] as a JSON string; reads it back as list[float]."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)
