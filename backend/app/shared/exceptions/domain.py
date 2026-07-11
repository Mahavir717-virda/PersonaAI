"""Domain-level shared exceptions for feature slices."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain-layer failures."""


class DependencyBoundaryError(DomainError):
    """Raised when an import or dependency crosses an architectural boundary."""
