"""
Core Models Package

Exports base models e mixins per facile import nelle app.
"""

from .base import BaseModel, BaseModelWithCode, BaseModelSimple

__all__ = ["BaseModel", "BaseModelWithCode", "BaseModelSimple"]


def __getattr__(name):
    """Lazy import from legacy models for backward compatibility"""
    if name in (
        "Allegato",
        "ModuloRegistry",
        "TimestampMixin",
        "SoftDeleteMixin",
        "AllegatiMixin",
        "AuditMixin",
        "UserTrackingMixin",
        "ModuloRegistryManager",
        "AuditLog",
        "allegato_upload_path",
    ):
        from .. import models_legacy

        return getattr(models_legacy, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
