"""Tests for constraint_store.py — extract and persist user constraints."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.memory.constraint_store import add_constraint, get_user_constraints


class TestGetUserConstraints:
    def test_extracts_hard_constraints_from_allergies(self):
        user = MagicMock()
        user.allergies = ["paraben", "sulfate"]
        user.preferences = {}

        hard, soft = get_user_constraints(user)
        assert hard == ["paraben", "sulfate"]
        assert soft == []

    def test_extracts_soft_preferences_from_dict(self):
        user = MagicMock()
        user.allergies = []
        user.preferences = {"fragrance_free": True, "vegan": True}

        hard, soft = get_user_constraints(user)
        assert hard == []
        assert "fragrance_free: True" in soft
        assert "vegan: True" in soft

    def test_extracts_soft_preferences_from_list(self):
        user = MagicMock()
        user.allergies = []
        user.preferences = ["fragrance_free", "vegan"]

        hard, soft = get_user_constraints(user)
        assert hard == []
        assert soft == ["fragrance_free", "vegan"]

    def test_handles_none_allergies(self):
        user = MagicMock()
        user.allergies = None
        user.preferences = None

        hard, soft = get_user_constraints(user)
        assert hard == []
        assert soft == []

    def test_handles_empty_allergies(self):
        user = MagicMock()
        user.allergies = []
        user.preferences = {}

        hard, soft = get_user_constraints(user)
        assert hard == []
        assert soft == []

    def test_handles_non_list_allergies(self):
        """Non-list allergies value should return empty hard_constraints."""
        user = MagicMock()
        user.allergies = "paraben"
        user.preferences = None

        hard, soft = get_user_constraints(user)
        assert hard == []

    def test_returns_copy_not_reference(self):
        """Returned list should be a copy, not a reference to user.allergies."""
        user = MagicMock()
        user.allergies = ["paraben"]
        user.preferences = {}

        hard, _ = get_user_constraints(user)
        hard.append("sulfate")
        assert "sulfate" not in user.allergies


class TestAddConstraint:
    @pytest.mark.asyncio
    async def test_add_hard_constraint_appends_to_allergies(self):
        user = MagicMock()
        user.allergies = ["paraben"]
        user.preferences = {}

        result = MagicMock()
        result.scalar_one_or_none.return_value = user

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        await add_constraint(db, "user-123", "sulfate", is_hard=True)
        assert "sulfate" in user.allergies
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_hard_constraint_skips_duplicate(self):
        user = MagicMock()
        user.allergies = ["paraben"]
        user.preferences = {}

        result = MagicMock()
        result.scalar_one_or_none.return_value = user

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        await add_constraint(db, "user-123", "paraben", is_hard=True)
        assert user.allergies.count("paraben") == 1

    @pytest.mark.asyncio
    async def test_add_soft_constraint_sets_preference(self):
        user = MagicMock()
        user.allergies = []
        user.preferences = {}

        result = MagicMock()
        result.scalar_one_or_none.return_value = user

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        await add_constraint(db, "user-123", "vegan", is_hard=False)
        assert user.preferences["vegan"] is True

    @pytest.mark.asyncio
    async def test_add_constraint_user_not_found(self):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        # Should not raise, just return
        await add_constraint(db, "nonexistent", "paraben", is_hard=True)
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_hard_constraint_with_none_allergies(self):
        user = MagicMock()
        user.allergies = None
        user.preferences = {}

        result = MagicMock()
        result.scalar_one_or_none.return_value = user

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        await add_constraint(db, "user-123", "sulfate", is_hard=True)
        assert "sulfate" in user.allergies

    @pytest.mark.asyncio
    async def test_add_soft_constraint_with_none_preferences(self):
        user = MagicMock()
        user.allergies = []
        user.preferences = None

        result = MagicMock()
        result.scalar_one_or_none.return_value = user

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)

        await add_constraint(db, "user-123", "vegan", is_hard=False)
        # preferences was None, so it gets initialized
        # The code checks isinstance(preferences, dict) which is True for {}
        assert user.preferences is not None
