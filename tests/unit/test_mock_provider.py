from datetime import date, datetime

import pytest

from court_alerts.core.diff import find_opened_slots
from court_alerts.core.models import CLUB_TZ
from court_alerts.providers.base import ProviderError, ScheduleProvider
from court_alerts.providers.mock import (
    MockProvider,
    failing_provider,
    make_day,
    open_slot,
)

TODAY = date(2026, 8, 24)
COURTS = ["Court 1", "Court 2"]
CLUB = "centreville"


def test_mock_provider_satisfies_the_protocol():
    provider = MockProvider([make_day(TODAY, COURTS)])
    assert isinstance(provider, ScheduleProvider)


def test_snapshots_replay_in_order_and_feed_the_diff():
    full = make_day(TODAY, COURTS)
    after_cancellation = open_slot(full, "Court 1", 19)
    provider = MockProvider([full, after_cancellation])

    before = provider.fetch_slots(CLUB, TODAY)
    after = provider.fetch_slots(CLUB, TODAY)
    opened = find_opened_slots(before, after)

    assert len(opened) == 1
    assert opened[0].court == "Court 1"
    assert opened[0].start == datetime(2026, 8, 24, 19, tzinfo=CLUB_TZ)


def test_final_step_repeats_after_the_script_runs_out():
    full = make_day(TODAY, COURTS)
    provider = MockProvider([full])

    first = provider.fetch_slots(CLUB, TODAY)
    second = provider.fetch_slots(CLUB, TODAY)

    assert first == second
    assert provider.calls == 2


def test_scripted_failure_is_raised_with_evidence():
    provider = failing_provider("upstream returned 503", CLUB, TODAY)

    with pytest.raises(ProviderError) as caught:
        provider.fetch_slots(CLUB, TODAY)

    evidence = caught.value.as_evidence()
    assert evidence["error_type"] == "ProviderError"
    assert evidence["club_id"] == CLUB
    assert evidence["on_date"] == "2026-08-24"


def test_callers_cannot_mutate_the_scripted_snapshot():
    full = make_day(TODAY, COURTS)
    provider = MockProvider([full])

    returned = provider.fetch_slots(CLUB, TODAY)
    returned.clear()

    assert len(provider.fetch_slots(CLUB, TODAY)) == len(full)