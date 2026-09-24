# airflow-local

Local Apache Airflow 3.3.2, run via Docker Compose (CeleryExecutor + Postgres + Redis).

## Quick start

```bash
docker compose up -d       # start
docker compose ps          # check status
docker compose down        # stop (keeps DB volume)
docker compose down -v     # stop and wipe DB volume
```

UI: http://localhost:8080

DAGs go in `./dags` — picked up automatically, no restart needed.

## Containers

| Container | Role |
|---|---|
| `postgres` | Metadata DB — DAG state, task history, connections, users |
| `redis` | Message broker — queues tasks between scheduler and workers |
| `airflow-apiserver` | Serves the web UI + REST API (port 8080) |
| `airflow-scheduler` | Decides what should run and when, queues tasks |
| `airflow-dag-processor` | Parses DAG files in `./dags`, separate from the scheduler |
| `airflow-worker` | Celery worker — actually executes tasks |
| `airflow-triggerer` | Runs deferred/async tasks (e.g. sensors waiting on external events) without blocking a worker slot |

## How this compares to a production deployment

**Similar** — same architecture, same code path:

- Every role above exists in production Airflow too; this isn't a simplified topology, just single-instance.
- DAG parsing, scheduling, and execution are decoupled the same way in prod — that split exists for scalability/security isolation.
- DAGs written here run unmodified in production — that's the point of matching the execution model locally.

**Different** — this is single-node; production is distributed and hardened:

| Aspect | Here | Production |
|---|---|---|
| Executor/workers | 1 Celery worker container | KubernetesExecutor (task = pod) or CeleryExecutor with many autoscaled worker replicas |
| Scheduler/apiserver | 1 of each | Multiple replicas for HA, behind a load balancer |
| Metadata DB | Postgres container, local volume, no backups | Managed DB (RDS/Cloud SQL), backups, read replicas, pgbouncer |
| Broker | Redis container, no persistence | Managed Redis/RabbitMQ cluster, persistent, failover |
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
