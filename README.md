# airflow-ai

Local Apache Airflow 3.3.2, run via Docker Compose (LocalExecutor + Postgres).

## What is this?

Hi! This is actually me. This repo contains example work and exploration of the AI tasks, operators, and tools available to Airflow. These are pretty neat and likely underused.

These examples are done with Claude but could be easily reworked to use Codex, etc.

## Quick start

```bash
docker compose up -d       # start
docker compose ps          # check status
docker compose down        # stop (keeps DB volume)
docker compose down -v     # stop and wipe DB volume
```

UI: http://localhost:8080

DAGs go in `./dags` — picked up automatically, no restart needed.

After changing `requirements.txt` or the `Dockerfile`, rebuild: `docker compose build && docker compose up -d`.

## Example DAGs

All use the `anthropic_default` connection and are tagged `claude`.

| DAG | Demonstrates |
|---|---|
| `llm_task_example` | `@task.llm` — unstructured and structured (`output_type`) responses |
| `llm_branch_example` | `@task.llm_branch` |
| `llm_sql_example` | `@task.llm_sql` — question to SQL against `dwh_default` (logged, not executed) |
| `llm_file_analysis_example` | `@task.llm_file_analysis` — downloads a Kaggle CSV at run time (not stored in the repo) and analyzes it |
| `task_agent_example` | `@task.agent` with `SQLToolset` |
| `task_failure_triage_example` | LLM-based failure triage |

## Manual restart

If Docker Desktop isn't running, start it first and wait for the daemon:

```bash
open -a Docker
until docker info >/dev/null 2>&1; do sleep 2; done
```

Then restart the stack:

```bash
docker compose restart     # containers already exist — restart in place
docker compose up -d       # containers don't exist yet (or after `down`) — (re)create and start
docker compose ps          # confirm everything is healthy
```

## Containers

| Container | Role |
|---|---|
| `postgres` | Metadata DB — DAG state, task history, connections, users |
| `airflow-apiserver` | Serves the web UI + REST API (port 8080) |
| `airflow-scheduler` | Decides what should run and when, executes tasks directly as subprocesses (LocalExecutor) |
| `airflow-dag-processor` | Parses DAG files in `./dags`, separate from the scheduler |
| `airflow-triggerer` | Runs deferred/async tasks (e.g. sensors waiting on external events) without blocking a worker slot |
| `dwh` | Toy data warehouse — Postgres, standing in for something like Redshift |
| `dwh-fetch` | One-off: downloads the Weimar Jazz Database (`wjazzd.db`, SQLite) fresh on every `up` |
| `dwh-seed` | One-off: loads `wjazzd.db` into `dwh` via `pgloader`, runs after `dwh-fetch` |

## Data warehouse (`dwh`)

A second Postgres instance, separate from Airflow's own metadata DB, seeded with real toy data (jazz solo transcriptions) on every `docker compose up` — good for testing DAGs that query a warehouse.

Airflow connection: `dwh_default` (see `config/connections.yaml`).

Query it directly from the terminal:

```bash
docker exec -it airflow-local-dwh-1 psql -U dwh -d dwh
# or, from the host, since dwh is published on 5433:
psql -h localhost -p 5433 -U dwh -d dwh
```

Tables: `melody`, `beats`, `sections`, `solo_info`, `transcription_info`, `track_info`, `record_info`, `composition_info`, and a few others — see the [Weimar Jazz Database docs](https://jazzomat.hfm-weimar.de/dbformat/dbformat.html) for schema details.

Re-seeding is idempotent (`pgloader` drops/recreates tables), so `docker compose up -d dwh-fetch dwh-seed` re-downloads and reloads on demand.

## Missing from this repo

`config/` and `.env` are gitignored and not committed — bring your own:

- `.env` — `AIRFLOW_UID`, `FERNET_KEY`
- `config/connections.yaml` — must include `anthropic_default` (`conn_type: pydanticai`, Anthropic API key as `password`, `extra.model`) and `dwh_default`
- `config/variables.yaml`

# TODO

- @task.llm_schema_compare (could be hard to test)
- HookToolset
- SQLToolset
- MCPToolset
- DataFusionToolset
- PydanticAIHook
- HITL


# References

- https://airflow.apache.org/blog/common-ai-provider/
- https://airflow.apache.org/docs/apache-airflow-providers-common-ai/stable/operators/llm.html
