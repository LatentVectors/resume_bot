# LangGraph Deploy Interaction Guide

This document provides a comprehensive guide for interacting with LangGraph Deploy. Follow these rules to ensure correct and efficient operation.

## Core Concepts

- **Assistant**: A deployed LangGraph graph. An assistant can be configured with specific parameters.
- **Thread**: A persistent sequence of operations and state. A thread is independent of any single assistant; multiple different assistants can be run on the same thread.
- **Run**: A single execution of a graph. Runs can be stateful (associated with a thread) or stateless.

## General Guidelines

### MUST DO

- **Manage Resources**: Always delete cron jobs when they are no longer needed to prevent unintended executions and costs.
- **Use Stateless Runs**: Default to stateless runs when state persistence across multiple calls is not required. This simplifies resource management.
- **Use Background Runs**: For long-running graphs, use background runs to avoid blocking client operations.

### AVOID

- **Leaking Sensitive Data**: Be cautious with `configurable_headers`. `excludes` takes precedence over `includes`. To be safest, explicitly exclude sensitive headers like `authorization`.
- **Leaving Cron Jobs**: Do not create cron jobs without a corresponding plan to delete them.

## API Interaction

### Client Initialization

```python
from langgraph_sdk import get_client

client = get_client(url=<DEPLOYMENT_URL>)
```

---

### Runs

There are multiple ways to execute runs depending on the need for state persistence and execution time.

#### Stateless Runs

Use for single-turn interactions where no memory is needed. This is the simplest way to execute a run. The `thread_id` is `None`.

- **Blocking (wait for result)**:
  ```python
  # Returns the final state of the graph
  result = await client.runs.wait(None, assistant_id, input=input)
  ```
- **Streaming**:
  ```python
  # Yields intermediate chunks or updates from the graph execution
  async for chunk in client.runs.stream(
      None, assistant_id, input=input, stream_mode="updates"
  ):
      # Process chunk
  ```

#### Stateful Runs (on a Thread)

Use when you need to persist state across multiple interactions.

1.  **Create a Thread**: A thread holds the state.
    ```python
    thread = await client.threads.create()
    # thread["thread_id"] is the identifier
    ```
2.  **Execute on the Thread**: Use the `thread_id` to run an assistant. The state will be loaded and saved back to the thread.
    ```python
    async for event in client.runs.stream(
        thread["thread_id"], assistant_id, input=input
    ):
        # Process events
    ```
    - Multiple different assistants can be run on the same thread, allowing them to share and build upon the same state.

#### Background Runs

Use for long-running tasks to avoid blocking the client.

1.  **Create a Run**: Initiates the run and returns immediately.
    ```python
    run = await client.runs.create(thread["thread_id"], assistant_id, input=input)
    # run["run_id"] is the identifier for this specific run
    ```
2.  **Check Run Status**: Poll the status of the run.
    ```python
    status = await client.runs.get(thread["thread_id"], run["run_id"])
    ```
3.  **Wait for Completion**: Block until the run is finished.
    ```python
    final_state = await client.runs.join(thread["thread_id"], run["run_id"])
    ```
    - To wait for multiple background runs concurrently, use `asyncio.gather`.

---

### Cron Jobs

Schedule assistants to run at specified intervals.

- **Schedule Format**: Cron expressions are used (`minute hour day_of_month month day_of_week`). All schedules are in UTC.

- **Stateless Cron Job**: The graph is invoked with only the specified input.

  ```python
  cron_job = await client.crons.create(
      assistant_id,
      schedule="0 9 * * MON-FRI",  # 9 AM UTC every weekday
      input=input,
  )
  ```

- **Stateful Cron Job**: The graph is invoked on a specific thread, loading and saving its state.
  ```python
  cron_job = await client.crons.create_for_thread(
      thread["thread_id"],
      assistant_id,
      schedule="0 0 1 * *", # Midnight UTC on the 1st of every month
      input=input,
  )
  ```
- **Deletion (CRITICAL)**: Always delete cron jobs when they are no longer needed.
  ```python
  await client.crons.delete(cron_job["cron_id"])
  ```

---

### Configuration via Headers

Pass dynamic configuration to the graph on a per-request basis using HTTP headers.

- **Enable in `langgraph.json`**:

  ```json
  {
    "http": {
      "configurable_headers": {
        "includes": ["x-user-id", "my-prefix-*"],
        "excludes": ["authorization"]
      }
    }
  }
  ```

  - `excludes` has higher priority than `includes`.
  - Use `excludes: ["*"]` to disable this feature entirely.

- **Accessing Headers in the Graph**:

  - Header names are **lower-cased** when accessed in the config.
  - **In Nodes**: Access via the `config` parameter.
    ```python
    def my_node(state, config):
        user_id = config["configurable"].get("x-user-id")
        # ...
    ```
  - **In Tools/Functions**: Use the `get_config` helper.

    ```python
    from langgraph.config import get_config

    def my_tool():
        user_id = get_config()["configurable"].get("x-user-id")
        # ...
    ```

# Resources

https://docs.langchain.com/langsmith/background-run
https://docs.langchain.com/langsmith/same-thread
https://docs.langchain.com/langsmith/cron-jobs
https://docs.langchain.com/langsmith/stateless-runs
https://docs.langchain.com/langsmith/configurable-headers
