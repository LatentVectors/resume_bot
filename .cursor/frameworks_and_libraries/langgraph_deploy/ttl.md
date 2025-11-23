# LangGraph Deploy: Time-to-Live (TTL) Configuration

This document provides guidelines for configuring Time-to-Live (TTL) policies for data persisted by LangGraph Deploy. TTL automatically manages the lifecycle of persisted data, preventing indefinite accumulation. Configuration is managed via the `langgraph.json` file.

## MUST

- Define TTL policies in the `langgraph.json` file.
- Restart or re-deploy the application for TTL configuration changes to take effect.
- Understand that `default_ttl` applies only to data created _after_ the configuration is deployed.
- Manually delete existing data if you need to clear items created before a TTL policy was active.

## AVOID

- Assuming TTL configurations affect existing checkpoints or store items. They do not.
- Omitting `sweep_interval_minutes` for store items if you want them to be periodically deleted. Without it, no sweeping occurs.

---

## 1. Checkpoint TTL

Checkpoints capture the state of conversation threads. A TTL policy on checkpoints ensures old threads are automatically deleted.

### Configuration

Add a `checkpointer.ttl` object to `langgraph.json`.

```json
{
  "checkpointer": {
    "ttl": {
      "strategy": "delete",
      "sweep_interval_minutes": 60,
      "default_ttl": 43200
    }
  }
}
```

### Arguments

- `strategy`: (string) Action on expiration. Only `"delete"` is currently supported. Deletes all checkpoints in the thread.
- `sweep_interval_minutes`: (integer) Frequency in minutes for the system to check for and delete expired checkpoints.
- `default_ttl`: (integer) Default lifespan of a thread in minutes (e.g., `43200` = 30 days).

---

## 2. Store Item TTL

Store items enable cross-thread data persistence. A TTL policy manages this data to prevent staleness.

### Configuration

Add a `store.ttl` object to `langgraph.json`.

```json
{
  "store": {
    "ttl": {
      "refresh_on_read": true,
      "sweep_interval_minutes": 120,
      "default_ttl": 10080
    }
  }
}
```

### Arguments

- `refresh_on_read`: (boolean, optional, default: `true`) If `true`, accessing an item via `get` or `search` resets its TTL timer. If `false`, TTL only refreshes on `put`.
- `sweep_interval_minutes`: (integer, optional) Frequency in minutes to check for and delete expired items. If omitted, no sweeping occurs.
- `default_ttl`: (integer, optional) Default lifespan of store items in minutes (e.g., `10080` = 7 days). If omitted, items do not expire by default.

---

## 3. Combined Configuration

Configure TTLs for both checkpoints and store items in the same `langgraph.json` file.

```json
{
  "checkpointer": {
    "ttl": {
      "strategy": "delete",
      "sweep_interval_minutes": 60,
      "default_ttl": 43200
    }
  },
  "store": {
    "ttl": {
      "refresh_on_read": true,
      "sweep_interval_minutes": 120,
      "default_ttl": 10080
    }
  }
}
```

---

## 4. Per-Thread and Runtime Overrides

### Per-Thread TTL

Apply a specific TTL when creating a new thread via the SDK. This overrides the `langgraph.json` default for that thread.

```python
thread = await client.threads.create(
    ttl={
        "strategy": "delete",
        "ttl": 43200  # 30 days in minutes
    }
)
```

### Runtime Overrides

The `store.ttl` settings can be overridden at runtime by providing TTL values in SDK method calls like `get`, `put`, and `search`.

---

## 5. Deployment Process

After modifying TTL settings in `langgraph.json`, you must re-deploy or restart the application for the changes to take effect. Use `langgraph dev` for local development or `langgraph up` for Docker deployments.

---

## Resources

- https://docs.langchain.com/langsmith/configure-ttl
