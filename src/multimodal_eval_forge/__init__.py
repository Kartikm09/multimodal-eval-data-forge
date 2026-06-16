"""Synthetic multimodal evaluation dataset utilities."""

from .forge import generate_dataset
from .validator import validate_records

__all__ = ["generate_dataset", "validate_records"]
