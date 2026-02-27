"""
Unit tests for Phase 1 — Periodic Collection backend changes.

Covers:
  1. Ad.last_seen_at field — model serialisation / deserialisation
  2. AdRepo.create_or_update — sets last_seen_at on new and existing ads
  3. NicheRepo.list_all_with_auto_collect — DynamoDB Scan filter
  4. CollectionRepo.get_latest_for_niche — delegates to list_for_niche
  5. collect_scheduler handler — should_collect logic + fan-out behaviour

Run from the aws_lambda_deploy directory:
    pytest tests/test_phase1_periodic_collection.py -v
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER_PATH = os.path.join(REPO_ROOT, "lambda_layers", "shared", "python")
SCHEDULER_PATH = os.path.join(REPO_ROOT, "lambda_src", "collect_scheduler")

for p in (LAYER_PATH, SCHEDULER_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import importlib.util

from app.dynamodb.models import Ad, Niche, CollectionRun
from app.dynamodb.collection_repo import CollectionRepo

# Load collect_scheduler/handler.py with a unique module name to avoid
# collision with lambda_src/niches/handler.py which pytest may have already
# imported as the bare name "handler" (Python module cache keyed by name).
# Registering in sys.modules is required for patch("collect_scheduler_handler.X")
# to resolve the module correctly.
_spec = importlib.util.spec_from_file_location(
    "collect_scheduler_handler",
    os.path.join(SCHEDULER_PATH, "handler.py"),
)
scheduler_handler = importlib.util.module_from_spec(_spec)
sys.modules["collect_scheduler_handler"] = scheduler_handler
_spec.loader.exec_module(scheduler_handler)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ad(**kwargs) -> Ad:
    defaults = dict(
        id="ad-uuid-1",
        niche_id="niche-uuid-1",
        meta_ad_id="meta-ad-111",
        page_id="page-1",
        page_name="Test Page",
        body="Buy now",
        collected_at="2026-02-01T00:00:00+00:00",
        last_seen_at="",
    )
    defaults.update(kwargs)
    return Ad(**defaults)


def _make_niche(**kwargs) -> Niche:
    defaults = dict(
        id="niche-uuid-1",
        user_id="user-1",
        name="AI Video",
        slug="ai-video",
        keywords=["ai video", "opus clip"],
        countries=["US"],
        platforms=["instagram"],
        auto_collect_enabled=True,
        auto_collect_interval_hours=3,
    )
    defaults.update(kwargs)
    return Niche(**defaults)


def _make_run(**kwargs) -> CollectionRun:
    defaults = dict(
        id="run-uuid-1",
        niche_id="niche-uuid-1",
        status="completed",
        keywords_used=["ai video"],
        ads_found=10,
        ads_new=2,
        ads_updated=8,
        error_message=None,
        started_at="2026-02-27T00:00:00+00:00",
        completed_at="2026-02-27T00:05:00+00:00",
    )
    defaults.update(kwargs)
    return CollectionRun(**defaults)


# ---------------------------------------------------------------------------
# 1. Ad model — last_seen_at field
# ---------------------------------------------------------------------------

class TestAdLastSeenAt:

    def test_last_seen_at_default_is_empty_string(self):
        ad = _make_ad()
        assert ad.last_seen_at == ""

    def test_to_item_includes_last_seen_at(self):
        ad = _make_ad(last_seen_at="2026-02-27T12:00:00+00:00")
        item = ad.to_item()
        assert "last_seen_at" in item
        assert item["last_seen_at"] == "2026-02-27T12:00:00+00:00"

    def test_from_item_deserialises_last_seen_at(self):
        ad = _make_ad(last_seen_at="2026-02-27T12:00:00+00:00")
        item = ad.to_item()
        restored = Ad.from_item(item)
        assert restored.last_seen_at == "2026-02-27T12:00:00+00:00"

    def test_from_item_missing_last_seen_at_defaults_to_empty(self):
        """Backward compat: existing DynamoDB items without last_seen_at."""
        ad = _make_ad()
        item = ad.to_item()
        item.pop("last_seen_at", None)  # simulate legacy item
        restored = Ad.from_item(item)
        assert restored.last_seen_at == ""

    def test_to_dict_includes_last_seen_at(self):
        ad = _make_ad(last_seen_at="2026-02-27T12:00:00+00:00")
        d = ad.to_dict()
        assert "last_seen_at" in d
        assert d["last_seen_at"] == "2026-02-27T12:00:00+00:00"


# ---------------------------------------------------------------------------
# 2. AdRepo.create_or_update — last_seen_at assignment
# ---------------------------------------------------------------------------

class TestAdRepoLastSeenAt:

    @patch("app.dynamodb.ad_repo.get_table")
    @patch("app.dynamodb.ad_repo.AdRepo.get")
    @patch("app.dynamodb.ad_repo.now_iso8601", return_value="2026-02-27T10:00:00+00:00")
    @patch("app.dynamodb.ad_repo.generate_uuid", return_value="new-uuid")
    def test_new_ad_gets_last_seen_at(self, mock_uuid, mock_now, mock_get, mock_table):
        from app.dynamodb.ad_repo import AdRepo

        mock_get.return_value = None  # ad does not exist yet
        mock_table.return_value = MagicMock()

        ad = _make_ad(id="", collected_at="", last_seen_at="")
        result, is_new = AdRepo.create_or_update(ad)

        assert is_new is True
        assert result.last_seen_at == "2026-02-27T10:00:00+00:00"
        assert result.collected_at == "2026-02-27T10:00:00+00:00"

    @patch("app.dynamodb.ad_repo.get_table")
    @patch("app.dynamodb.ad_repo.AdRepo.get")
    @patch("app.dynamodb.ad_repo.now_iso8601", return_value="2026-02-27T10:00:00+00:00")
    def test_existing_ad_updates_last_seen_at_but_preserves_collected_at(
        self, mock_now, mock_get, mock_table
    ):
        from app.dynamodb.ad_repo import AdRepo

        existing = _make_ad(
            id="existing-id",
            collected_at="2026-02-01T00:00:00+00:00",
            last_seen_at="2026-02-20T00:00:00+00:00",
        )
        mock_get.return_value = existing
        mock_table.return_value = MagicMock()

        incoming = _make_ad(id="", collected_at="", last_seen_at="")
        result, is_new = AdRepo.create_or_update(incoming)

        assert is_new is False
        # collected_at is immutable — must preserve original
        assert result.collected_at == "2026-02-01T00:00:00+00:00"
        # last_seen_at is updated to now
        assert result.last_seen_at == "2026-02-27T10:00:00+00:00"


# ---------------------------------------------------------------------------
# 3. NicheRepo.list_all_with_auto_collect
# ---------------------------------------------------------------------------

class TestNicheRepoListAllWithAutoCollect:

    @patch("app.dynamodb.niche_repo.get_table")
    def test_returns_only_auto_collect_niches(self, mock_get_table):
        from app.dynamodb.niche_repo import NicheRepo

        niche = _make_niche()
        item = niche.to_item()

        table = MagicMock()
        # Single page scan result
        table.scan.return_value = {"Items": [item]}
        mock_get_table.return_value = table

        result = NicheRepo.list_all_with_auto_collect()

        assert len(result) == 1
        assert result[0].id == "niche-uuid-1"
        assert result[0].auto_collect_enabled is True

    @patch("app.dynamodb.niche_repo.get_table")
    def test_paginates_through_multiple_scan_pages(self, mock_get_table):
        from app.dynamodb.niche_repo import NicheRepo

        niche_a = _make_niche(id="niche-a", slug="niche-a")
        niche_b = _make_niche(id="niche-b", slug="niche-b")

        table = MagicMock()
        table.scan.side_effect = [
            {"Items": [niche_a.to_item()], "LastEvaluatedKey": {"PK": "USER#x", "SK": "NICHE#a"}},
            {"Items": [niche_b.to_item()]},
        ]
        mock_get_table.return_value = table

        result = NicheRepo.list_all_with_auto_collect()

        assert len(result) == 2
        assert {n.id for n in result} == {"niche-a", "niche-b"}
        assert table.scan.call_count == 2

    @patch("app.dynamodb.niche_repo.get_table")
    def test_returns_empty_list_when_no_opt_in_niches(self, mock_get_table):
        from app.dynamodb.niche_repo import NicheRepo

        table = MagicMock()
        table.scan.return_value = {"Items": []}
        mock_get_table.return_value = table

        result = NicheRepo.list_all_with_auto_collect()
        assert result == []


# ---------------------------------------------------------------------------
# 4. CollectionRepo.get_latest_for_niche
# ---------------------------------------------------------------------------

class TestCollectionRepoGetLatest:

    @patch.object(CollectionRepo, "list_for_niche")
    def test_returns_first_run_when_present(self, mock_list):
        run = _make_run()
        mock_list.return_value = [run]

        result = CollectionRepo.get_latest_for_niche("niche-uuid-1")

        mock_list.assert_called_once_with("niche-uuid-1", limit=1)
        assert result is run

    @patch.object(CollectionRepo, "list_for_niche")
    def test_returns_none_when_no_runs(self, mock_list):
        mock_list.return_value = []

        result = CollectionRepo.get_latest_for_niche("niche-uuid-1")
        assert result is None


# ---------------------------------------------------------------------------
# 5. collect_scheduler handler — _should_collect logic
# ---------------------------------------------------------------------------

class TestShouldCollect:

    def test_no_previous_run_returns_true(self):
        niche = _make_niche()
        assert scheduler_handler._should_collect(niche, latest_run=None) is True

    def test_run_with_no_completed_at_returns_false(self):
        niche = _make_niche()
        run = _make_run(completed_at=None, status="running")
        assert scheduler_handler._should_collect(niche, run) is False

    def test_run_completed_before_interval_returns_false(self):
        niche = _make_niche(auto_collect_interval_hours=3)
        # completed 1 hour ago — not yet due
        one_hour_ago = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
        run = _make_run(completed_at=one_hour_ago)
        assert scheduler_handler._should_collect(niche, run) is False

    def test_run_completed_after_interval_returns_true(self):
        niche = _make_niche(auto_collect_interval_hours=3)
        # completed 4 hours ago — due
        four_hours_ago = (datetime.now(tz=timezone.utc) - timedelta(hours=4)).isoformat()
        run = _make_run(completed_at=four_hours_ago)
        assert scheduler_handler._should_collect(niche, run) is True

    def test_run_completed_exactly_at_interval_returns_true(self):
        niche = _make_niche(auto_collect_interval_hours=3)
        # completed exactly 3 hours ago — due (>=)
        three_hours_ago = (datetime.now(tz=timezone.utc) - timedelta(hours=3)).isoformat()
        run = _make_run(completed_at=three_hours_ago)
        assert scheduler_handler._should_collect(niche, run) is True

    def test_unparseable_completed_at_returns_true(self):
        niche = _make_niche()
        run = _make_run(completed_at="not-a-date")
        assert scheduler_handler._should_collect(niche, run) is True


# ---------------------------------------------------------------------------
# 6. collect_scheduler handler — Lambda handler fan-out
# ---------------------------------------------------------------------------

class TestSchedulerHandler:

    def _run_handler(self, niches, latest_run=None, worker_arn="arn:aws:lambda:us-east-1:111:function:worker"):
        """Helper: patch repos + boto3 and invoke handler."""
        with (
            patch.dict(os.environ, {"COLLECT_WORKER_ARN": worker_arn, "AWS_REGION": "us-east-1"}),
            patch("collect_scheduler_handler.NicheRepo.list_all_with_auto_collect", return_value=niches),
            patch("collect_scheduler_handler.CollectionRepo.get_latest_for_niche", return_value=latest_run),
            patch("collect_scheduler_handler.CollectionRepo.create") as mock_create,
            patch("collect_scheduler_handler.CollectionRepo.mark_error") as mock_mark_error,
            patch("collect_scheduler_handler.generate_uuid", return_value="run-uuid-x"),
            patch("collect_scheduler_handler.now_iso8601", return_value="2026-02-27T12:00:00+00:00"),
            patch("boto3.client") as mock_boto,
        ):
            mock_lambda_client = MagicMock()
            mock_boto.return_value = mock_lambda_client
            result = scheduler_handler.handler({}, None)
            return result, mock_create, mock_mark_error, mock_lambda_client

    def test_no_opt_in_niches_returns_zero_invocations(self):
        result, mock_create, _, mock_lambda = self._run_handler(niches=[])
        assert result["niches_found"] == 0
        assert result["invocations"] == 0
        mock_lambda.invoke.assert_not_called()

    def test_niche_without_keywords_is_skipped(self):
        niche = _make_niche(keywords=[])
        result, mock_create, _, mock_lambda = self._run_handler(niches=[niche])
        assert result["skipped"] == 1
        assert result["invocations"] == 0
        mock_lambda.invoke.assert_not_called()

    def test_niche_not_yet_due_is_skipped(self):
        niche = _make_niche(auto_collect_interval_hours=3)
        recent_run = _make_run(
            completed_at=(datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
        )
        result, _, _, mock_lambda = self._run_handler(niches=[niche], latest_run=recent_run)
        assert result["skipped"] == 1
        mock_lambda.invoke.assert_not_called()

    def test_fan_out_one_invocation_per_keyword(self):
        niche = _make_niche(keywords=["ai video", "opus clip"])
        result, mock_create, _, mock_lambda = self._run_handler(niches=[niche])

        # Two keywords → two CollectionRun creates and two invoke calls
        assert mock_create.call_count == 2
        assert mock_lambda.invoke.call_count == 2
        assert result["invocations"] == 2

    def test_invoked_payload_contains_expected_fields(self):
        niche = _make_niche(keywords=["ai video"])
        _, _, _, mock_lambda = self._run_handler(niches=[niche])

        call_kwargs = mock_lambda.invoke.call_args[1]
        payload = json.loads(call_kwargs["Payload"])

        assert payload["niche_id"] == niche.id
        assert payload["keyword"] == "ai video"
        assert payload["run_id"] == "run-uuid-x"
        assert payload["started_at"] == "2026-02-27T12:00:00+00:00"
        assert payload["limit"] == 50
        assert call_kwargs["InvocationType"] == "Event"

    def test_invoke_failure_marks_run_error_and_continues(self):
        niche = _make_niche(keywords=["ai video", "opus clip"])
        with (
            patch.dict(os.environ, {"COLLECT_WORKER_ARN": "arn:aws:lambda:::func", "AWS_REGION": "us-east-1"}),
            patch("collect_scheduler_handler.NicheRepo.list_all_with_auto_collect", return_value=[niche]),
            patch("collect_scheduler_handler.CollectionRepo.get_latest_for_niche", return_value=None),
            patch("collect_scheduler_handler.CollectionRepo.create"),
            patch("collect_scheduler_handler.CollectionRepo.mark_error") as mock_mark_error,
            patch("collect_scheduler_handler.generate_uuid", side_effect=["run-1", "run-2"]),
            patch("collect_scheduler_handler.now_iso8601", return_value="2026-02-27T12:00:00+00:00"),
            patch("boto3.client") as mock_boto,
        ):
            mock_lambda_client = MagicMock()
            # First invoke succeeds, second fails
            mock_lambda_client.invoke.side_effect = [None, RuntimeError("throttled")]
            mock_boto.return_value = mock_lambda_client

            result = scheduler_handler.handler({}, None)

        # One invocation succeeded, one failed → mark_error called once
        assert mock_mark_error.call_count == 1
        assert result["invocations"] == 1

    def test_missing_worker_arn_raises_runtime_error(self):
        import pytest
        env = {k: v for k, v in os.environ.items() if k != "COLLECT_WORKER_ARN"}
        with patch.dict(os.environ, env, clear=True):
            # Ensure COLLECT_WORKER_ARN is absent
            os.environ.pop("COLLECT_WORKER_ARN", None)
            try:
                scheduler_handler.handler({}, None)
                assert False, "Expected RuntimeError"
            except RuntimeError as exc:
                assert "COLLECT_WORKER_ARN" in str(exc)
