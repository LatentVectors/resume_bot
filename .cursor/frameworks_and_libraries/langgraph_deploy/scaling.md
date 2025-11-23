# LangGraph Deploy Guide

This document provides guidelines for configuring, scaling, and interacting with a deployed LangGraph application on the LangSmith Agent Server.

## Core Concepts

A deployed LangGraph is managed by the Agent Server, which consists of three main components:

1.  **API Server**: Handles synchronous requests (reads, creating runs).
2.  **Queue Worker**: Executes runs asynchronously.
3.  **Persistence Layer**: Postgres for storing all data and Redis for ephemeral run data.

Scaling involves tuning these components based on workload.

## Scaling for Write Load

Write load is driven by creating runs, threads, assistants, and checkpoints.

### DOs

- **Tune Worker Jobs**: Adjust the `N_JOBS_PER_WORKER` environment variable (default: 10).
  - Increase for I/O-bound assistants to handle more concurrent runs per worker.
  - Decrease for CPU-bound assistants if you observe high CPU usage.
- **Use Asynchronous Code**: Prefer `asyncio.sleep()` over `time.sleep()` and other async operations to avoid blocking the main event loop.
- **Minimize Checkpointing**: If only the final state is needed, set durability to `exit` when creating a run. This reduces writes by only storing the final state.
  ```python
  run = await client.runs.create(
      thread_id=thread["thread_id"],
      assistant_id="agent",
      durability="exit"
  )
  ```
- **(Self-Hosted) Enable Queue Workers**: For high write loads, offload run execution from the API server to dedicated queue workers.
  ```yaml
  # In your values.yaml
  queue:
    enabled: true
  ```

### DON'Ts

- **Avoid Synchronous Blocking**: Do not use long-running synchronous operations. If unavoidable, set the `BG_JOB_ISOLATED_LOOPS=True` environment variable to execute each run in a separate event loop.
- **Avoid Over-Provisioning `N_JOBS_PER_WORKER`**: Setting this value too high in bursty traffic environments can lead to uneven worker utilization and increased run latency.

---

## Scaling for Read Load

Read load is driven by getting run results, thread states, and searching for resources.

### DOs

- **Filter Search Queries**: Use the filtering capabilities of the search APIs to limit the amount of data returned per request.
- **Set TTLs**: Set a Time-To-Live (TTL) on threads to automatically clean up old data. Runs and checkpoints are deleted when the parent thread is deleted.
- **Use Streaming Endpoints**: To monitor a run's progress, use the `/stream` endpoint for real-time output or the `/join` endpoint to wait for the final result.

### DON'Ts

- **Avoid Polling**: Do not repeatedly poll the status of a run. Use the `/join` or `/stream` endpoints instead, which are designed for this purpose.

---

## Self-Hosted Configuration Examples

These configurations are for managing the `values.yaml` in a self-hosted deployment. Resources are per replica.

| Load Profile           | Read RPS | Write RPS | API Servers | Queue Workers | `N_JOBS_PER_WORKER` | Postgres CPU/Mem |
| ---------------------- | -------- | --------- | ----------- | ------------- | ------------------- | ---------------- |
| Low / Low              | 5        | 5         | 1           | 1             | 10                  | 2 CPU / 8Gi      |
| Low Read / High Write  | 5        | 500       | 6           | 10            | 50                  | 4 CPU / 16Gi     |
| High Read / Low Write  | 500      | 5         | 10          | 1             | 10                  | 4 CPU / 16Gi     |
| Medium / Medium        | 50       | 50        | 3           | 5             | 10                  | 4 CPU / 16Gi     |
| High Read / High Write | 500      | 500       | 15          | 10            | 50                  | 8 CPU / 32Gi     |

### Autoscaling for Bursty Traffic

Enable autoscaling in your configuration to handle variable loads.

```yaml
# In your values.yaml
api:
  autoscaling:
    enabled: true
    minReplicas: 15
    maxReplicas: 25
queue:
  autoscaling:
    enabled: true
    minReplicas: 10
    maxReplicas: 20
```

---

## Key Configuration Parameters

These are set as environment variables on the Agent Server or in the deployment configuration file.

- `N_JOBS_PER_WORKER`: (Default: 10) Number of concurrent runs a single queue worker can execute.
- `BG_JOB_ISOLATED_LOOPS`: (Default: `False`) If `True`, executes each background job (run) in a separate, isolated event loop. Use for graphs with synchronous blocking code.
- `queue.enabled`: (Default: `false` for self-hosted) If `true`, enables dedicated queue workers for run execution.
- `api.replicas`: Number of API server replicas.
- `queue.replicas`: Number of queue worker replicas.
- `api.autoscaling.enabled`: (Default: `false`) Enables autoscaling for API servers.
- `queue.autoscaling.enabled`: (Default: `false`) Enables autoscaling for queue workers.

## Resources

- [Configure LangSmith Agent Server for scale](https://docs.langchain.com/langsmith/agent-server-scale)
