# court-alerts

A read-only monitor that watches pickleball court availability at a
Life Time club and sends a Discord alert when a booked slot opens up.
Failed polls are classified by an LLM triage agent whose output is
validated, bounded, and never trusted.

---

## The problem

Life Time does have a waitlist notification system. The catch is that
each waitlist has a cap on how many members can join it. Once that cap
is reached, everyone else is shut out — and a member who is not on the
list gets no notification at all when a spot opens.

So the gap is not "there is no feature." The gap is that access to the
feature is rationed, and the people it excludes are exactly the ones
who need it. Cancellations happen constantly; without a notification
you only find them by refreshing the booking page yourself.

## On permission

Before writing any code against a real Life Time endpoint, I emailed
the club and their corporate concierge describing exactly what this
tool would do: read-only, personal use, no automated booking, polling
at a low fixed interval.

The reply confirmed the capped-waitlist behaviour described above,
raised no objection to the tool, and said the feedback had been passed
to the club's pickleball team and their development team. It did not
give an explicit written answer on terms of use.

**Because that answer never came, this repository ships no real Life
Time adapter.** The only implementation is a deterministic mock. The
schedule source sits behind a `ScheduleProvider` interface, so adding
a real adapter later means adding one file — not changing the core.

That was a design decision and a compliance decision at the same time.

---

## Run it in 60 seconds

No API keys required. Without secrets the app falls back to console
output and rule-based triage.

```bash
docker compose up -d          # Postgres on port 5433
uv sync
uv run court-alerts demo      # two poll cycles against the mock
```

Expected output:

```
Club: Life Time Centreville  Date: 2026-08-24  Notifier: console
cycle 1: status=ok slots=64 opened=0 alerts=0
cycle 2: status=ok slots=64 opened=2 alerts=1
```

Cycle 1 is a cold start on a fully booked day, so nothing is new.
Cycle 2 introduces two cancellations, which are detected and delivered
as a **single batched message**.

To use real integrations, copy `.env.example` to `.env` and fill in
`DISCORD_WEBHOOK_URL`, `GEMINI_API_KEY`, and `GEMINI_MODEL`.

Other commands:

```bash
uv run court-alerts triage             # classify the recent poll history
uv run court-alerts eval               # score the LLM against the golden set
uv run court-alerts eval --agent heuristic
uv run pytest -q                       # 51 tests
```

---

## Architecture

Dependencies point inward only. Nothing in `core/` imports a provider,
a database, or an HTTP client.

```
core/models.py        Slot, CLUB_TZ            (imports nothing)
       ^
core/diff.py          cancellation detection
core/subscription.py  who cares about which slot
       ^
providers/base.py     ScheduleProvider contract
notify/base.py        Notifier contract
triage/base.py        TriageAgent contract
       ^
providers/mock.py  notify/discord.py  triage/gemini.py  db/
       ^
poller.py             the only place these meet
```

Consequences:

- The 43 unit tests run in under 0.5s with no database and no network.
- Swapping the mock provider for a real one touches one file.
- Every boundary that can fail has a matching in-process implementation
  (`MockProvider`, `ConsoleNotifier`, `HeuristicTriageAgent`), so the
  whole pipeline runs offline with zero secrets.

### Data model

Snapshots are append-only. Each poll writes a `snapshots` row plus its
`snapshot_slots`, and every attempt — successful or not — writes a
`poll_runs` row. Nothing is updated in place, so a crashed poll cannot
corrupt the previous state, and the run history is the raw material
the triage agent reads.

All timestamps are `timestamptz`, converted back to club-local time on
read. Storing naive datetimes would have made the same wall-clock hour
ambiguous twice a year during the DST fall-back.

---

## Trade-off: at-least-once delivery

`run_poll` commits the snapshot **before** attempting delivery.

If delivery then fails, the worst case is one duplicated alert on the
next cycle. If the order were reversed and the snapshot were lost, the
next cycle would be a cold start — and every open court on the schedule
would alert at once.

One duplicate is recoverable. An alert storm trains the user to mute
the channel, which silently destroys the whole point of the tool.

This is enforced by a test: after a forced delivery failure, the
following cycle must report zero new openings.

---

## LLM failure triage

When a poll fails, the interesting question is not *that* it failed but
*what kind* of failure it was — a timeout worth retrying, an expired
credential, or an upstream schema change that needs a code fix. Those
three look identical in structured fields and differ only in free-text
error messages. That is where a language model earns its place.

Four safeguards, each addressing a specific failure mode:

**1. Bounded evidence, not raw exceptions.**
`build_evidence()` constructs a flat JSON bundle from an explicit list
of fields. Exception objects, response bodies, and config are never
copied wholesale. A webhook URL or API key has no path into a prompt —
not because a filter removes it, but because the container was never
built to hold it.

**2. Explicit escape hatches.**
`TriageCategory` includes `NO_ISSUE` and `UNKNOWN`, and the prompt
states that guessing is worse than admitting uncertainty. A classifier
with no way to say "nothing is wrong" will invent a problem for healthy
runs; one with no way to say "I can't tell" will fabricate a diagnosis
from a one-line error.

**3. Validate, fall back, never raise.**
`parse_verdict()` trusts nothing: non-JSON output, an invented category
string, a confidence of `"high"` or `7.5`, a missing field, or a
markdown-fenced response all resolve to a valid verdict rather than an
exception. Unrecognised categories become `UNKNOWN`; confidence is
clamped to `[0, 1]`; `needs_human` defaults to `True`. `safe_triage()`
wraps everything as a last line of defence.

**4. Retry only what retrying can fix.**
HTTP 429 and 5xx are retried with exponential backoff. 401 and 404 are
not — the same request will produce the same answer.

### This was tested by accident

During development the API produced three different failures in one
afternoon: a misconfigured model name returning 404 on every request,
a 503 under load, and read timeouts. The poller kept working through
all of them, every verdict came back `UNKNOWN` with `needs_human=True`,
and **not one incorrect diagnosis was produced**. The 404 case also
confirmed safeguard 4 from the other direction — retrying a name that
does not exist would only have wasted the job's runtime.

The observability layer degraded without damaging the thing it observes.

---

## Evaluation

`evals/cases.py` holds 12 hand-labelled evidence bundles covering three
kinds of judgement:

- **Discrimination** — `expired_session`, `forbidden`, `shape_changed`
  are all `status=provider_failed`; only the error text distinguishes
  them, and each demands a different response.
- **False-positive resistance** — `recovered_delivery` and
  `quiet_but_healthy` contain alarming-looking history that is actually
  fine.
- **Honest uncertainty** — `no_history` and `uninformative_error` have
  `unknown` as the correct answer.

| Agent | Category accuracy |
|---|---|
| `HeuristicTriageAgent` (rules) | **8 / 12** |
| `GeminiTriageAgent` | _TBD_ |

The rule-based baseline fails in a way that is structural, not
tunable. It collapses `expired_session`, `forbidden`, and
`shape_changed` into `transient_upstream` because it never reads the
error text, and it asserts `transient_upstream` for
`uninformative_error` because rules have no concept of "I don't know."
Regex could patch the first three until the upstream rewrites its
error strings.

The baseline exists so the LLM has something to beat. Reporting an
LLM's accuracy without one says nothing.

---

## Testing

51 tests. Unit tests cover pure logic with no I/O; integration tests
run against Postgres on a **separate database**, each inside a
transaction that is rolled back.

That separation was added after a real failure: the integration tests
originally shared the application database, so running the demo made a
cold-start test fail. Test outcomes depended on what had been run
before — which is a test suite that lies.

Three tests are worth calling out:

- `test_snapshot_survives_a_delivery_failure` pins the at-least-once
  trade-off above.
- `test_scoring_a_crashing_agent_does_not_raise` proves triage cannot
  take down the poller, across all 12 golden cases.
- `test_factory_falls_back_to_console_without_a_webhook` exists because
  `notify/factory.py` was once empty while all 32 tests passed — the
  assembly code had nothing testing it.

## Secrets

`.env` is gitignored; `.env.example` documents the required keys with
no values. The Gemini key is sent as an `x-goog-api-key` header rather
than a `?key=` query parameter, so it cannot leak through URLs in proxy
logs or exception messages — which is what makes it safe for the error
handler to include a truncated response body in its diagnostics.

Discord's own exceptions embed the full webhook URL, so
`DiscordNotifier` carries forward only the exception class name.

## Not built yet

- **Real Life Time adapter** — gated on a written answer about terms of
  use. The interface is ready.
- **Alembic migrations** — `create_all()` covers a schema that is still
  moving. This was consciously deprioritised below the eval set.
- **Web UI** — subscriptions are hard-coded in `cli.py`. A Vite + React
  frontend for creating subscriptions, viewing detected openings, and
  reviewing triage verdicts is the next step.
- **Deployment** — designed for Cloud Run Jobs (every run is a fresh
  process, which is why state lives in Postgres), but not yet deployed.