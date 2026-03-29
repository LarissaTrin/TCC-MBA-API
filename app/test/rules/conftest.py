"""Shared fixtures and helpers for rules tests."""
from unittest.mock import AsyncMock, MagicMock
import pytest

# Register models NOT included in app/db/models/__init__.py so that SQLAlchemy
# can resolve relationship strings (e.g. CardModel → "CategoryModel") when
# model instances are created during tests.
# These imports use the "app.db.models.*" path (same as the rules modules) and
# do NOT conflict with test_tag_card_model.py because those tests never import
# these four models via the "db.models.*" path.
import app.db.models.category_model       # noqa: F401
import app.db.models.card_history_model   # noqa: F401
import app.db.models.card_dependency_model  # noqa: F401
import app.db.models.user_notes_model     # noqa: F401


def make_session():
    """Returns a mock AsyncSession with all async methods pre-configured."""
    s = MagicMock()
    s.execute = AsyncMock()
    s.add = MagicMock()
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    s.delete = AsyncMock()
    s.flush = AsyncMock()
    s.rollback = AsyncMock()
    return s


def make_result(scalar=None, scalars_list=None, scalar_val=None):
    """
    Builds a mock result object that supports the most common SQLAlchemy
    result access patterns used across the rules layer.
    """
    r = MagicMock()
    # result.scalar_one_or_none()
    r.scalar_one_or_none.return_value = scalar
    # result.scalar()
    r.scalar.return_value = scalar_val if scalar_val is not None else (scalar or 0)
    # result.unique().scalar_one_or_none()
    r.unique.return_value.scalar_one_or_none.return_value = scalar
    # result.unique().scalars().all()
    r.unique.return_value.scalars.return_value.all.return_value = scalars_list or []
    # result.scalars().unique().one_or_none()
    r.scalars.return_value.unique.return_value.one_or_none.return_value = scalar
    # result.scalars().unique().all()
    r.scalars.return_value.unique.return_value.all.return_value = scalars_list or []
    # result.scalars().all()
    r.scalars.return_value.all.return_value = scalars_list or []
    # result.scalars().one_or_none()
    r.scalars.return_value.one_or_none.return_value = scalar
    # result.unique().all()
    r.unique.return_value.all.return_value = scalars_list or []
    return r
