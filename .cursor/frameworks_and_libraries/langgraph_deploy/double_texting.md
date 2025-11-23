# LangGraph Deploy Interaction Guide

This document provides concise guidelines for an LLM to interact with LangGraph applications deployed via LangSmith.

## 1. Overview

LangGraph Deploy allows running stateful, multi-actor applications built with LangGraph as persistent services. Interaction occurs via a REST API, enabling operations on conversational threads and managing concurrent requests. State is maintained on the server, identified by a `thread_id`.

## 2. Core API Interaction

Interaction is managed through an SDK client.

```python
from langgraph_sdk import get_client

# The URL of the LangGraph deployment
deployment_url = "..."
client = get_client(url=deployment_url)

# The ID of the specific graph assistant to run
assistant_id = "my-assistant-id"
```

### 2.1. Threads

Threads represent persistent states of the graph, typically a single conversation.

- **Create a new thread**: A new thread is required for each distinct, stateful conversation.
  ```python
  thread = await client.threads.create()
  thread_id = thread["thread_id"]
  ```

### 2.2. Runs

Runs are executions of the graph within a specific thread.

- **Create a new run**: This invokes the graph with new input for a given thread.
  ```python
  run = await client.runs.create(
      thread_id,
      assistant_id,
      input={"messages": [{"role": "user", "content": "..."}]},
      # See Section 3 for multitask_strategy
  )
  run_id = run["run_id"]
  ```
- **Wait for a run to complete**: This is a crucial step to ensure the run has finished processing before proceeding.
  ```python
  # Polls until the run is in a terminal state
  await client.runs.join(thread_id, run_id)
  ```

### 2.3. State Management

- **Get the current state of a thread**:
  ```python
  state = await client.threads.get_state(thread_id)
  # The current values are in state["values"]
  ```

## 3. Concurrency Control (`multitask_strategy`)

When a new run is created on a thread that already has a run in progress (a "double-text"), the `multitask_strategy` argument in `client.runs.create()` controls the behavior.

- **`reject`** (Default Behavior):

  - **Action**: Rejects the new run, returning a `409 Conflict` error. The original run continues unaffected.
  - **Use Case**: Prevent any concurrent modifications. Ensure one operation completes before starting another.
  - **Code**: `multitask_strategy="reject"`

- **`enqueue`**:

  - **Action**: Places the new run in a queue. It will execute only after the original run completes. Runs are processed sequentially in the order they were received.
  - **Use Case**: Process all user inputs in order, without interruption.
  - **Code**: `multitask_strategy="enqueue"`

- **`interrupt`**:

  - **Action**: Stops the original run, preserving its state up to the point of interruption. The new run then starts immediately from that preserved state. The interrupted run's status becomes `'interrupted'`.
  - **Use Case**: Allow a user to correct or redirect the agent mid-task while keeping the history of the first attempt.
  - **Code**: `multitask_strategy="interrupt"`

- **`rollback`**:
  - **Action**: Stops and completely deletes the original run, reverting the thread's state to what it was before that run began. The new run then starts from the reverted state.
  - **Use Case**: Allow a user to completely discard the previous command and start over from a clean slate. The history of the first attempt is erased from the thread's state history.
  - **Code**: `multitask_strategy="rollback"`

## 4. Key Guidelines

### MUST DO:

1.  **Always use a `thread_id`** to maintain conversational state. Create a new one for each distinct conversation.
2.  **Explicitly choose a `multitask_strategy`** when creating a run if the default behavior (`reject`) is not desired. This is critical for managing user interruptions.
3.  **Wait for run completion** using `client.runs.join()` before inspecting the final state to ensure all operations have finished.
4.  **Handle potential HTTP errors**. A `409 Conflict` when using the `reject` strategy is expected behavior, not a server failure.
5.  When using `interrupt`, ensure the graph is designed to be resilient to being stopped at any step.

### AVOID:

1.  **Do not create a new thread for every message** within the same conversation. This defeats the purpose of stateful execution.
2.  **Do not assume runs complete instantly**. They are asynchronous operations that must be waited for.
3.  **Do not use `rollback` if you need to keep a record** of the interrupted task's progress. Use `interrupt` instead.
4.  **Do not forget the `assistant_id`** when creating runs; it specifies which deployed graph to execute.

## Resources

- https://docs.langchain.com/langsmith/double-texting
- https://docs.langchain.com/langsmith/interrupt-concurrent
- https://docs.langchain.com/langsmith/rollback-concurrent
- https://docs.langchain.com/langsmith/reject-concurrent
- https://docs.langchain.com/langsmith/enqueue-concurrent
