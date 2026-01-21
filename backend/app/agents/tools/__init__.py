"""Tools for LLM-based therapy sentence generation.

This package provides tools for the 4-stage generation pipeline:
1. Generate - Generate candidate sentences using LLM
2. Validate - Validate phoneme requirements
3. Score - Score sentences based on quality metrics
4. Diversify - Ensure diversity in final selection
"""

from .generate import generate_candidates

__all__ = ["generate_candidates"]
