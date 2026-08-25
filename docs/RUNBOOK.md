# Runbook

Operational commands for court-alerts. Day-to-day work is in the
`Makefile`; this file covers the things you do rarely enough to forget.

## Variables

Cloud commands assume these. Paste this block into a fresh shell first —
a partial `gcloud run jobs update` with an empty variable will silently
erase configuration.

```bash
export PROJECT_ID=court-alerts-1787559454
export REGION=us-east1
export INSTANCE=court-alerts-db
export REPO=court-alerts
export SA_EMAIL="court-alerts-job@${PROJECT_ID}.iam.gserviceaccount.com"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/poller:v1"
export CONNECTION_NAME="$(gcloud sql instances describe $INSTANCE --format='value(connectionName)')"
```

Verify before doing anything destructive:

```bash
echo "$REGION / $CONNECTION_NAME / $SA_EMAIL / $IMAGE"
```

---

## Cost control

The scheduled job costs almost nothing. The Cloud SQL instance is the
expense — roughly $25–30/month while running.

**Stop the alerts and the spend:**

```bash
gcloud scheduler jobs pause court-alerts-schedule --location=$REGION
gcloud sql instances patch $INSTANCE --activation-policy=NEVER
```

Order matters. Pause the scheduler first — stopping the database while
the job still fires produces a socket error that looks like a
misconfiguration and is not.

**Start it back up (~2 minutes):**

```bash
gcloud sql instances patch $INSTANCE --activation-policy=ALWAYS
gcloud sql instances describe $INSTANCE --format='value(state)'   # wait for RUNNABLE
gcloud scheduler jobs resume court-alerts-schedule --location=$REGION
```

Stopped is not deleted. Storage still bills at roughly $1–2/month, and
the connection name stays the same — deleting and recreating would
change it and break the job's configuration.

---

## Local development

```bash
docker compose up -d                                    # Postgres on 5433
make test                                               # 53 tests
make demo                                               # two poll cycles
uv run uvicorn court_alerts.api.app:app --port 8000     # API
cd web && npm run dev                                   # UI on 5173
```

Always run `pytest` and `alembic` from the repo root. Both look for
config files relative to the current directory, and running from a
subdirectory silently skips tests or fails to find `alembic.ini`.

**Reset the local database:**

```bash
docker compose down -v && docker compose up -d
sleep 8
uv run alembic upgrade head
```

**Produce a failed run** (for the dashboard or for triage):

```bash
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1/bad" \
  uv run court-alerts demo
uv run court-alerts triage
```

---

## Schema changes

Order is not optional. Autogenerate compares the models against the
current database, so editing the models *after* generating produces an
empty migration that still applies cleanly.

```bash
# 1. edit src/court_alerts/db/tables.py
# 2. generate
uv run alembic revision --autogenerate -m "describe the change"

# 3. VERIFY — never skip this
grep -c 'add_column\|create_table' migrations/versions/*<slug>*.py

# 4. apply
uv run alembic upgrade head
uv run alembic current
make test
```

If autogenerate reports no changes but you did edit the models, the
database is probably already at that shape. Drop it and rebuild:

```bash
docker compose down -v && docker compose up -d && sleep 8
uv run alembic upgrade head
```

Undo an unapplied mistake:

```bash
uv run alembic downgrade -1
rm migrations/versions/<the bad file>.py
```

---

## Deploying a code change

Pass `--set-cloudsql-instances` on every update. A partial update drops
it without warning, and the next run fails on a socket path that has
simply stopped being mounted.

```bash
make test
docker build -t $IMAGE . && docker push $IMAGE

gcloud run jobs update court-alerts-poller \
  --region=$REGION \
  --image=$IMAGE \
  --set-cloudsql-instances=$CONNECTION_NAME

gcloud run jobs execute court-alerts-poller --region=$REGION --wait
```

Confirm the connection survived:

```bash
gcloud run jobs describe court-alerts-poller --region=$REGION --format=yaml \
  | grep cloudsql
```

---

## Reading logs

`--freshness` defaults to a narrow window and will return nothing.
Widen it before concluding there are no logs.

```bash
# errors in the last half hour, tail only
gcloud logging read \
  'resource.type="cloud_run_job" AND severity>=ERROR' \
  --limit=1 --freshness=30m --format='value(textPayload)' | tail -5

# everything from the most recent execution
EXEC=$(gcloud run jobs executions list --job=court-alerts-poller \
  --region=$REGION --limit=1 --format='value(name)')
gcloud logging read \
  "resource.type=\"cloud_run_job\" AND labels.\"run.googleapis.com/execution_name\"=\"$EXEC\"" \
  --limit=50 --format='value(textPayload)' | tail -20
```

Drop the `severity` filter when a run fails silently — the last stdout
line before the traceback tells you how far it got.

Execution status:

```bash
gcloud run jobs executions list --job=court-alerts-poller --region=$REGION --limit=5 \
  --format='table(name, metadata.creationTimestamp, status.succeededCount, status.failedCount)'
```

An empty count column means zero, not "still running" — check the
timestamp.

---

## Secrets

Strip `\r` when piping from `.env`. CRLF line endings put a carriage
return inside the stored secret, which produces an `InvalidURL` that
reads like a code bug.

```bash
grep '^DISCORD_WEBHOOK_URL=' .env | cut -d= -f2- | tr -d '\r\n' \
  | gcloud secrets versions add discord-webhook-url --data-file=-
```

`--data-file=-` reads stdin, so the value never enters shell history.
The job references `:latest`, so a new version takes effect on the next
run with no redeploy.

Check length, never value:

```bash
for s in db-password discord-webhook-url gemini-api-key; do
  echo "$s: $(gcloud secrets versions access latest --secret=$s | wc -c) bytes"
done
```

---

## Gemini model names

A 404 means the name does not exist for this key — retrying will not
help. List what the key can actually reach:

```bash
source .env
curl -s -H "x-goog-api-key: $GEMINI_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models" \
| uv run python -c "
import json, sys
data = json.load(sys.stdin)
for model in data.get('models', []):
    if 'generateContent' in model.get('supportedGenerationMethods', []):
        print(model['name'])
"
```

Put the name in `.env` as `GEMINI_MODEL` **without** the `models/`
prefix — the endpoint template adds it.

---

## Symptom → cause

| Symptom | Actual cause |
|---|---|
| `No such file or directory` on the Cloud SQL socket | Instance stopped, or `--set-cloudsql-instances` was dropped by a partial update |
| Job fails with no logs at all | `logging.googleapis.com` not enabled |
| `InvalidURL` from httpx | CRLF in `.env` left a `\r` in a secret |
| Gemini returns 404 on every call | `GEMINI_MODEL` is not a name this key can reach |
| Gemini returns 503 or times out | Upstream load; the retry path handles it, wait and re-run |
| Tests pass but the app is broken | Assembly code (factories, wiring) has no test touching it |
| Test count is lower than expected | Ran pytest from a subdirectory, or a file was never saved |
| Cold-start test fails after a demo | Test database and app database are not separated |