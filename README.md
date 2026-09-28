# airflow-local

Local Apache Airflow 3.3.2, run via Docker Compose (LocalExecutor + Postgres).

## Quick start

```bash
docker compose up -d       # start
docker compose ps          # check status
docker compose down        # stop (keeps DB volume)
docker compose down -v     # stop and wipe DB volume
```

UI: http://localhost:8080

DAGs go in `./dags` — picked up automatically, no restart needed.

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

## How this compares to a production deployment

**Similar** — same architecture, same code path:

- Every role above exists in production Airflow too; this isn't a simplified topology, just single-instance.
- DAG parsing and scheduling are decoupled from each other the same way in prod — that split exists for scalability/security isolation.
- DAGs written here run unmodified in production, regardless of executor — DAG code doesn't change based on how tasks get executed.

Note: with LocalExecutor, task **execution** is not decoupled — it runs as a subprocess of the scheduler here, unlike CeleryExecutor/KubernetesExecutor in prod where execution happens on separate workers/pods. If you need to test executor-specific behavior (queue routing, worker scaling, broker failure), that's the tradeoff for this setup's simplicity.

**Different** — this is single-node; production is distributed and hardened:

| Aspect | Here | Production |
|---|---|---|
| Executor/workers | LocalExecutor — scheduler runs tasks as subprocesses, no broker/worker split | KubernetesExecutor (task = pod) or CeleryExecutor with many autoscaled worker replicas + broker |
| Scheduler/apiserver | 1 of each | Multiple replicas for HA, behind a load balancer |
| Metadata DB | Postgres container, local volume, no backups | Managed DB (RDS/Cloud SQL), backups, read replicas, pgbouncer |
| Secrets | Plaintext in `.env` (Fernet key, JWT secret) | Secrets backend — Vault, AWS Secrets Manager, K8s secrets |
| DAG delivery | Bind-mounted local folder, live edits | git-sync sidecar, bucket sync, or baked into image via CI/CD |
| Image | Stock `apache/airflow` image | Custom-built image with pinned providers/deps, versioned in CI |
| Networking | Ports open on localhost, no TLS | Ingress/LB with TLS, private networking, SSO/OIDC auth manager |
| Orchestration | Docker Compose, single host | Kubernetes/ECS/managed service (MWAA, Cloud Composer, Astronomer), multi-node |
| Observability | `docker compose logs` | StatsD/Prometheus/Grafana metrics, centralized log shipping, alerting |
| Availability | Every component is a single point of failure | Redundant across nodes/AZs |

This setup validates DAG logic and Airflow behavior, not production readiness — it doesn't tell you how it scales, survives a node dying, or holds up under real secrets/network policy.

## Login

Default: `airflow` / `airflow`
Admin: `kirk` / `admin`
