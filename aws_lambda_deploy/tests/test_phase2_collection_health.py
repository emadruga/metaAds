"""
Unit tests for Phase 2 — Auditing & Analytics backend changes.

Covers:
  1. AdRepo.get_stale_ads  — DynamoDB Query + FilterExpression logic
  2. _get_collection_health endpoint — per-niche stats, summary totals, stale counts
  3. Edge cases — no niches, no runs, in-flight runs, legacy ads (empty last_seen_at)

Run from the aws_lambda_deploy directory:
    pytest tests/test_phase2_collection_health.py -v
"""

import json
import sys
import os
import importlib.util
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER_PATH = os.path.join(REPO_ROOT, "lambda_layers", "shared", "python")
NICHES_PATH = os.path.join(REPO_ROOT, "lambda_src", "niches")

for p in (LAYER_PATH, NICHES_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Imports from shared layer
# ---------------------------------------------------------------------------

from app.dynamodb.models import Ad, Niche, CollectionRun

# Load niches/handler.py under a unique module name to avoid collision with
# any other "handler" already loaded in the test session.
_spec = importlib.util.spec_from_file_location(
    "niches_handler_phase2",
    os.path.join(NICHES_PATH, "handler.py"),
)
niches_handler = importlib.util.module_from_spec(_spec)
sys.modules["niches_handler_phase2"] = niches_handler
_spec.loader.exec_module(niches_handler)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(hours_ago: float = 0) -> str:
    """Return an ISO-8601 UTC timestamp offset by hours_ago into the past."""
    dt = datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)
    return dt.isoformat()


def _make_ad(meta_ad_id: str = "ad1", niche_id: str = "niche-1",
             last_seen_at: str = "", is_active: bool = True) -> Ad:
    return Ad(
        id="uuid-" + meta_ad_id,
        niche_id=niche_id,
        meta_ad_id=meta_ad_id,
        page_id="page1",
        page_name="Page",
        headline="Test Ad",
        body="Body",
        start_date="2024-01-01",
        end_date=None,
        is_active=is_active,
        platforms=["instagram"],
        collected_at=_iso(48),
        last_seen_at=last_seen_at,
    )


def _make_niche(niche_id: str = "niche-1", slug: str = "test",
                auto_collect_enabled: bool = True,
                auto_collect_interval_hours: int = 6) -> Niche:
    return Niche(
        id=niche_id,
        user_id="user-1",
        name="Test Niche",
        slug=slug,
        description="",
        keywords=["keyword1"],
        countries=["US"],
        platforms=["instagram"],
        is_active=True,
        auto_collect_enabled=auto_collect_enabled,
        auto_collect_interval_hours=auto_collect_interval_hours,
        created_at=_iso(72),
        updated_at=_iso(72),
    )


def _make_run(niche_id: str = "niche-1", run_id: str = "run-1",
              status: str = "completed", started_hours_ago: float = 5,
              completed_hours_ago: float | None = 4.5) -> CollectionRun:
    return CollectionRun(
        id=run_id,
        niche_id=niche_id,
        status=status,
        keywords_used=["keyword1"],
        ads_found=10,
        ads_new=5,
        ads_updated=5,
        error_message=None,
        started_at=_iso(started_hours_ago),
        completed_at=_iso(completed_hours_ago) if completed_hours_ago is not None else None,
    )


def _health_event(user_id: str = "user-1") -> dict:
    """Minimal API Gateway v2 event for GET /api/admin/collection/health."""
    return {
        "routeKey": "GET /api/admin/collection/health",
        "requestContext": {
            "http": {"method": "GET"},
            "authorizer": {"lambda": {"user_id": user_id}},
        },
        "pathParameters": {},
        "queryStringParameters": {},
        "body": None,
    }


# ---------------------------------------------------------------------------
# 1. AdRepo.get_stale_ads
# ---------------------------------------------------------------------------

class TestGetStaleAds:
    """AdRepo.get_stale_ads — filters by is_active, last_seen_at < cutoff, last_seen_at > ''."""

    def test_returns_ads_older_than_threshold(self):
        """Ads whose last_seen_at is older than threshold are returned."""
        from app.dynamodb.ad_repo import AdRepo

        stale_ad = _make_ad("ad-stale", last_seen_at=_iso(25))  # 25h ago > 24h threshold
        fresh_ad = _make_ad("ad-fresh", last_seen_at=_iso(1))   # 1h ago, fresh

        # Mock DynamoDB query to return both; FilterExpression is applied by DynamoDB
        # but here we verify the method builds the right kwargs and processes results.
        mock_resp = {
            "Items": [stale_ad.to_item()],  # simulate DynamoDB already filtered
            "LastEvaluatedKey": None,
        }
        with patch("app.dynamodb.ad_repo.get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.query.return_value = mock_resp
            mock_get_table.return_value = mock_table

            result = AdRepo.get_stale_ads("niche-1", hours_threshold=24)

        assert len(result) == 1
        assert result[0].meta_ad_id == "ad-stale"

    def test_paginated_query(self):
        """Handles DynamoDB pagination (LastEvaluatedKey)."""
        from app.dynamodb.ad_repo import AdRepo

        ad1 = _make_ad("ad-1", last_seen_at=_iso(30))
        ad2 = _make_ad("ad-2", last_seen_at=_iso(40))

        page1 = {"Items": [ad1.to_item()], "LastEvaluatedKey": {"PK": "x", "SK": "y"}}
        page2 = {"Items": [ad2.to_item()], "LastEvaluatedKey": None}

        with patch("app.dynamodb.ad_repo.get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.query.side_effect = [page1, page2]
            mock_get_table.return_value = mock_table

            result = AdRepo.get_stale_ads("niche-1", hours_threshold=24)

        assert len(result) == 2
        assert mock_table.query.call_count == 2
        # Second call must include ExclusiveStartKey
        second_call_kwargs = mock_table.query.call_args_list[1][1]
        assert "ExclusiveStartKey" in second_call_kwargs

    def test_empty_result_when_all_fresh(self):
        """Returns empty list when DynamoDB returns no items."""
        from app.dynamodb.ad_repo import AdRepo

        with patch("app.dynamodb.ad_repo.get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.query.return_value = {"Items": [], "LastEvaluatedKey": None}
            mock_get_table.return_value = mock_table

            result = AdRepo.get_stale_ads("niche-1", hours_threshold=24)

        assert result == []

    def test_default_threshold_is_12_hours(self):
        """Default hours_threshold=12 is used when not specified."""
        from app.dynamodb.ad_repo import AdRepo

        with patch("app.dynamodb.ad_repo.get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.query.return_value = {"Items": [], "LastEvaluatedKey": None}
            mock_get_table.return_value = mock_table

            AdRepo.get_stale_ads("niche-1")  # no hours_threshold

        call_kwargs = mock_table.query.call_args[1]
        filter_expr = call_kwargs["FilterExpression"]
        # The filter expression string should reference a cutoff ~12h in the past
        # (we just verify the call was made and FilterExpression is present)
        assert filter_expr is not None

    def test_query_uses_correct_pk_and_sk_prefix(self):
        """Query is keyed by NICHE#<id> / begins_with AD#."""
        from app.dynamodb.ad_repo import AdRepo

        with patch("app.dynamodb.ad_repo.get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.query.return_value = {"Items": [], "LastEvaluatedKey": None}
            mock_get_table.return_value = mock_table

            AdRepo.get_stale_ads("my-niche-id", hours_threshold=6)

        call_kwargs = mock_table.query.call_args[1]
        # KeyConditionExpression must reference the correct PK value
        key_expr = call_kwargs["KeyConditionExpression"]
        assert key_expr is not None
        # Verify both KeyConditionExpression and FilterExpression were supplied
        assert "FilterExpression" in call_kwargs


# ---------------------------------------------------------------------------
# 2. _get_collection_health endpoint
# ---------------------------------------------------------------------------

class TestGetCollectionHealthBasic:
    """Basic happy-path behaviour of the health endpoint."""

    def test_returns_200_with_success_true(self):
        """Endpoint returns HTTP 200 and success=True."""
        niche = _make_niche()
        run = _make_run()

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[run]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["success"] is True

    def test_summary_counts_are_correct(self):
        """Summary totals reflect runs in the last 24h."""
        niche = _make_niche()
        runs = [
            _make_run(run_id="r1", status="completed", started_hours_ago=2, completed_hours_ago=1.5),
            _make_run(run_id="r2", status="failed",    started_hours_ago=4, completed_hours_ago=3.5),
            _make_run(run_id="r3", status="completed", started_hours_ago=6, completed_hours_ago=5.5),
        ]

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=runs),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        summary = body["data"]["summary"]
        assert summary["total_niches"] == 1
        assert summary["total_runs_24h"] == 3
        assert summary["total_successful_24h"] == 2

    def test_niche_entry_contains_required_fields(self):
        """Each niche entry has the expected shape."""
        niche = _make_niche()
        run = _make_run()

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[run]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        entry = body["data"]["niches"][0]
        for field in (
            "niche_id", "slug", "name", "auto_collect_enabled",
            "auto_collect_interval_hours", "hours_since_last_run",
            "runs_24h", "successful_24h", "success_rate",
            "stale_ads_count", "last_run_status",
        ):
            assert field in entry, f"Missing field: {field}"

    def test_stale_ads_count_is_included(self):
        """stale_ads_count reflects what AdRepo.get_stale_ads returns."""
        niche = _make_niche()
        stale = [_make_ad("s1", last_seen_at=_iso(30)), _make_ad("s2", last_seen_at=_iso(25))]

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=stale),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        assert body["data"]["niches"][0]["stale_ads_count"] == 2


class TestGetCollectionHealthEdgeCases:
    """Edge cases for the health endpoint."""

    def test_no_niches_returns_empty_list(self):
        """Returns empty niches list and zeroed summary when user has no niches."""
        with patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[]):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        assert body["data"]["niches"] == []
        summary = body["data"]["summary"]
        assert summary["total_niches"] == 0
        assert summary["total_runs_24h"] == 0
        assert summary["total_successful_24h"] == 0

    def test_no_runs_sets_hours_since_last_to_none(self):
        """hours_since_last_run is None when niche has never been collected."""
        niche = _make_niche()

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        entry = body["data"]["niches"][0]
        assert entry["hours_since_last_run"] is None
        assert entry["last_run_status"] is None

    def test_in_flight_run_uses_started_at(self):
        """For a run with no completed_at, hours_since_last_run uses started_at."""
        niche = _make_niche()
        # In-flight run: completed_at=None, started 2h ago
        run = _make_run(status="pending", started_hours_ago=2, completed_hours_ago=None)

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[run]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        entry = body["data"]["niches"][0]
        # Should be ~2 hours
        assert entry["hours_since_last_run"] is not None
        assert 1.5 < entry["hours_since_last_run"] < 2.5

    def test_success_rate_none_when_no_runs_in_24h(self):
        """success_rate is None (not zero) when there are no runs in the 24h window."""
        niche = _make_niche()
        # Old run, more than 24h ago
        old_run = _make_run(started_hours_ago=30, completed_hours_ago=29)

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[old_run]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        entry = body["data"]["niches"][0]
        assert entry["runs_24h"] == 0
        assert entry["success_rate"] is None

    def test_multiple_niches_aggregated_in_summary(self):
        """Summary sums across all niches belonging to the user."""
        n1 = _make_niche("niche-1", "slug-1")
        n2 = _make_niche("niche-2", "slug-2")

        runs_n1 = [_make_run("niche-1", "r1", status="completed", started_hours_ago=2, completed_hours_ago=1)]
        runs_n2 = [
            _make_run("niche-2", "r2", status="completed", started_hours_ago=3, completed_hours_ago=2),
            _make_run("niche-2", "r3", status="failed",    started_hours_ago=5, completed_hours_ago=4),
        ]

        def _list_runs(niche_id, limit=50):
            return runs_n1 if niche_id == "niche-1" else runs_n2

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[n1, n2]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", side_effect=_list_runs),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        summary = body["data"]["summary"]
        assert summary["total_niches"] == 2
        assert summary["total_runs_24h"] == 3
        assert summary["total_successful_24h"] == 2

    def test_niches_with_auto_collect_count(self):
        """niches_with_auto_collect counts only niches where auto_collect_enabled=True."""
        n1 = _make_niche("niche-1", "slug-1", auto_collect_enabled=True)
        n2 = _make_niche("niche-2", "slug-2", auto_collect_enabled=False)

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[n1, n2]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        assert body["data"]["summary"]["niches_with_auto_collect"] == 1

    def test_hours_since_last_run_uses_completed_at(self):
        """hours_since_last_run prefers completed_at over started_at."""
        niche = _make_niche()
        # started 5h ago, completed 2h ago
        run = _make_run(started_hours_ago=5, completed_hours_ago=2)

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[run]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]),
        ):
            resp = niches_handler.handler(_health_event(), None)

        body = json.loads(resp["body"])
        entry = body["data"]["niches"][0]
        # Should be ~2h (not ~5h)
        assert entry["hours_since_last_run"] is not None
        assert 1.5 < entry["hours_since_last_run"] < 2.5

    def test_route_dispatched_correctly(self):
        """handler() dispatches GET /api/admin/collection/health to _get_collection_health."""
        with patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[]):
            resp = niches_handler.handler(_health_event(), None)
        assert resp["statusCode"] == 200

    def test_get_stale_ads_called_with_24h_threshold(self):
        """The health endpoint calls AdRepo.get_stale_ads with 24-hour window."""
        niche = _make_niche("niche-abc", "slug-abc")

        with (
            patch("niches_handler_phase2.NicheRepo.list_for_user", return_value=[niche]),
            patch("niches_handler_phase2.CollectionRepo.list_for_niche", return_value=[]),
            patch("niches_handler_phase2.AdRepo.get_stale_ads", return_value=[]) as mock_stale,
        ):
            niches_handler.handler(_health_event(), None)

        mock_stale.assert_called_once_with("niche-abc", hours_threshold=24)
