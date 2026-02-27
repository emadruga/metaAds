"""
Unit tests for niches/handler.py — Phase 0 auto-collect changes.

Run from the aws_lambda_deploy directory:
    pytest tests/test_niche_handler.py -v

No AWS credentials or DynamoDB connection needed — all repo calls are mocked.
"""

import json
import sys
import os
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup — makes the shared layer and the niches handler importable
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER_PATH = os.path.join(REPO_ROOT, "lambda_layers", "shared", "python")
HANDLER_PATH = os.path.join(REPO_ROOT, "lambda_src", "niches")

for p in (LAYER_PATH, HANDLER_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Imports (after path setup)
# ---------------------------------------------------------------------------

from app.dynamodb.models import Niche
import handler as niches_handler  # lambda_src/niches/handler.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(method: str, route: str, body: dict = None, path_params: dict = None) -> dict:
    """Build a minimal API Gateway v2 event dict."""
    return {
        "routeKey": f"{method} {route}",
        "requestContext": {
            "http": {"method": method},
            "authorizer": {"lambda": {"user_id": "test-user-123"}},
        },
        "pathParameters": path_params or {},
        "body": json.dumps(body) if body is not None else "{}",
    }


def _make_niche(**kwargs) -> Niche:
    """Return a minimal Niche dataclass instance."""
    defaults = dict(
        id="niche-uuid-1",
        user_id="test-user-123",
        name="Test Niche",
        slug="test-niche",
        description="",
        keywords=["ai video"],
        countries=["US"],
        platforms=["instagram"],
        is_active=True,
        auto_collect_enabled=False,
        auto_collect_interval_hours=3,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    defaults.update(kwargs)
    return Niche(**defaults)


# ---------------------------------------------------------------------------
# Test 1: Niche.from_item() defaults for existing items without new fields
# ---------------------------------------------------------------------------

class TestNicheModelDefaults:
    """Pure model tests — no mocking needed."""

    def test_from_item_defaults_auto_collect_enabled(self):
        """Existing DynamoDB items without auto_collect_enabled default to False."""
        item = {
            "id": "abc-123",
            "user_id": "user-1",
            "name": "Old Niche",
            "slug": "old-niche",
            "keywords": "[]",
            "countries": '["US"]',
            "platforms": '["instagram"]',
            # auto_collect_enabled intentionally absent
        }
        niche = Niche.from_item(item)
        assert niche.auto_collect_enabled is False

    def test_from_item_defaults_auto_collect_interval_hours(self):
        """Existing DynamoDB items without interval default to 3."""
        item = {
            "id": "abc-123",
            "user_id": "user-1",
            "name": "Old Niche",
            "slug": "old-niche",
            "keywords": "[]",
            "countries": '["US"]',
            "platforms": '["instagram"]',
            # auto_collect_interval_hours intentionally absent
        }
        niche = Niche.from_item(item)
        assert niche.auto_collect_interval_hours == 3

    def test_from_item_reads_auto_collect_enabled_true(self):
        """When flag is stored as True it is read back correctly."""
        item = {
            "id": "abc-123",
            "user_id": "user-1",
            "name": "New Niche",
            "slug": "new-niche",
            "keywords": "[]",
            "countries": '["US"]',
            "platforms": '["instagram"]',
            "auto_collect_enabled": True,
            "auto_collect_interval_hours": 6,
        }
        niche = Niche.from_item(item)
        assert niche.auto_collect_enabled is True
        assert niche.auto_collect_interval_hours == 6

    def test_to_dict_includes_new_fields(self):
        """to_dict() must expose both new fields to the API response."""
        niche = _make_niche(auto_collect_enabled=True, auto_collect_interval_hours=6)
        d = niche.to_dict()
        assert "auto_collect_enabled" in d
        assert d["auto_collect_enabled"] is True
        assert "auto_collect_interval_hours" in d
        assert d["auto_collect_interval_hours"] == 6

    def test_interval_stored_as_int(self):
        """DynamoDB may return Decimal — int() cast in from_item() must handle it."""
        from decimal import Decimal
        item = {
            "id": "abc-123",
            "user_id": "user-1",
            "name": "Niche",
            "slug": "niche",
            "keywords": "[]",
            "countries": '["US"]',
            "platforms": '["instagram"]',
            "auto_collect_interval_hours": Decimal("6"),
        }
        niche = Niche.from_item(item)
        assert niche.auto_collect_interval_hours == 6
        assert isinstance(niche.auto_collect_interval_hours, int)


# ---------------------------------------------------------------------------
# Tests 2–5: Handler — keyword validation + auto_collect fields
# ---------------------------------------------------------------------------

class TestCreateNiche:

    def test_create_with_6_keywords_returns_400(self):
        """POST /api/niches with 6 keywords must return 400."""
        event = _make_event("POST", "/api/niches", body={
            "name": "Test Niche",
            "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"],
        })

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = None
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "5 keywords" in body["error"]

    def test_create_with_exactly_5_keywords_returns_201(self):
        """POST /api/niches with exactly 5 keywords must succeed."""
        event = _make_event("POST", "/api/niches", body={
            "name": "Test Niche",
            "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
        })

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = None
            MockRepo.create.return_value = None
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert len(body["data"]["keywords"]) == 5

    def test_create_with_0_keywords_returns_201(self):
        """POST /api/niches with no keywords is still valid."""
        event = _make_event("POST", "/api/niches", body={"name": "Empty Kw Niche"})

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = None
            MockRepo.create.return_value = None
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 201


class TestUpdateNiche:

    def test_update_with_6_keywords_returns_400(self):
        """PATCH /api/niches/{slug} with 6 keywords must return 400."""
        event = _make_event(
            "PATCH", "/api/niches/{slug}",
            body={"keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"]},
            path_params={"slug": "test-niche"},
        )

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = _make_niche()
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "5 keywords" in body["error"]

    def test_update_auto_collect_enabled_true(self):
        """PATCH with auto_collect_enabled=True must call NicheRepo.update with the flag."""
        event = _make_event(
            "PATCH", "/api/niches/{slug}",
            body={"auto_collect_enabled": True},
            path_params={"slug": "test-niche"},
        )

        updated_niche = _make_niche(auto_collect_enabled=True)

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = _make_niche()
            MockRepo.update.return_value = updated_niche
            MockRepo.get.return_value = updated_niche
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["auto_collect_enabled"] is True

        # Confirm update was called with the flag
        MockRepo.update.assert_called_once()
        call_kwargs = MockRepo.update.call_args[1]
        assert call_kwargs.get("auto_collect_enabled") is True

    def test_update_invalid_interval_returns_400(self):
        """PATCH with auto_collect_interval_hours=99 must return 400."""
        event = _make_event(
            "PATCH", "/api/niches/{slug}",
            body={"auto_collect_interval_hours": 99},
            path_params={"slug": "test-niche"},
        )

        with patch("handler.NicheRepo") as MockRepo:
            MockRepo.get_by_slug.return_value = _make_niche()
            response = niches_handler.handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "interval" in body["error"].lower()

    def test_update_valid_intervals_are_accepted(self):
        """All four valid intervals (2, 3, 6, 12) must pass validation."""
        for interval in [2, 3, 6, 12]:
            event = _make_event(
                "PATCH", "/api/niches/{slug}",
                body={"auto_collect_interval_hours": interval},
                path_params={"slug": "test-niche"},
            )

            updated_niche = _make_niche(auto_collect_interval_hours=interval)

            with patch("handler.NicheRepo") as MockRepo:
                MockRepo.get_by_slug.return_value = _make_niche()
                MockRepo.update.return_value = updated_niche
                MockRepo.get.return_value = updated_niche
                response = niches_handler.handler(event, None)

            assert response["statusCode"] == 200, \
                f"Expected 200 for interval={interval}, got {response['statusCode']}"
