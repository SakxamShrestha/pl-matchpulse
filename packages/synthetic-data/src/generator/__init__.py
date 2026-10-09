"""Synthetic football match event generator (Ingest-stage data source)."""

from .events import generate_match, generate_matches

__all__ = ["generate_match", "generate_matches"]
