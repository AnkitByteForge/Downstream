"""Shared configuration conventions used across services.

Scoped narrowly to the one explicit cross-service convention named in the
frozen docs — see ids.py's module docstring for why.
"""

from shared_config.ids import ID_PREFIXES, EntityName, generate_id, is_valid_id

__all__ = ["ID_PREFIXES", "EntityName", "generate_id", "is_valid_id"]
