# LangGraph Deploy: Interaction Guide

This document provides concise guidelines for interacting with a deployed LangGraph application. The core functionality revolves around state management using checkpoints, enabling powerful features like Human-in-the-Loop (HITL) and time-travel debugging.

## Core Concepts

- **Threads**: A thread represents a single, persistent execution history, identified by a `thread_id`. It contains all checkpoints for a conversation or run.
- **Checkpoints**: A checkpoint is an immutable snapshot of the graph's `State` at a specific point in its execution. Each step in a graph's execution generates a checkpoint.
- **Human-in-the-Loop (HITL)**: The ability to programmatically pause a graph's execution at any node (`interrupt_before`/`interrupt_after`), allow for external (human or automated) review and modification of the state, and then resume execution.
- **Time Travel**: The mechanism for resuming execution from any prior checkpoint within a thread's history. You can replay the execution from that point or first modify the state to explore alternative execution paths. Modifying state creates a new, forked history.

## HITL and Time Travel Workflow

The following four steps are the fundamental interaction pattern for inspecting, modifying, and resuming graph execution.

### 1. Initiate Execution

Start a new execution on a new or existing thread.

1.  **Create a Thread**: Establish a persistent history container.
    ```python
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    ```
2.  **Run the Graph**: Invoke the graph with initial input. This will run until it finishes or hits an interruption point.
    ```python
    # assistant_id is the name of the deployed graph, e.g., "agent"
    result = await client.runs.wait(
        thread_id,
        assistant_id,
        input={"messages": ["hello"]}
    )
    ```

### 2. Identify a Checkpoint

To modify a past state or resume from an interruption, you must identify the target checkpoint.

- **Retrieve History**: Fetch the list of all historical checkpoints for a given thread. They are returned in reverse chronological order (most recent first).
  ```python
  states = await client.threads.get_history(thread_id)
  # Example: Select the second-to-last state
  selected_checkpoint = states[1]
  checkpoint_id = selected_checkpoint["checkpoint_id"]
  ```

### 3. Update State (Optional)

If you need to change the graph's course, modify its state at the selected checkpoint. This action creates a **new checkpoint** with the updated values.

- **Modify State**: Provide the new state values. The original checkpoint remains unchanged, and a new one is created, forking the history.
  ```python
  new_checkpoint_config = await client.threads.update_state(
      thread_id,
      values={"topic": "a new topic"},
      checkpoint_id=checkpoint_id
  )
  new_checkpoint_id = new_checkpoint_config["checkpoint_id"]
  ```

### 4. Resume Execution

Continue the graph's execution from a specific checkpoint (either the original one or the new one created by `update_state`).

- **Call `wait` or `stream` with `checkpoint_id`**: Set `input` to `None` and specify the `checkpoint_id` from which to resume.
  ```python
  await client.runs.wait(
      thread_id,
      assistant_id,
      input=None,
      checkpoint_id=new_checkpoint_id # Use the new ID if state was updated
  )
  ```

## Rules and Guidelines

### MUST DO

- Always create a thread for persistent executions using `client.threads.create()`.
- Use `client.threads.get_history(thread_id)` to find the correct `checkpoint_id` before attempting to time travel or resume.
- When resuming execution from any checkpoint, always pass `input=None`. The graph will use the state saved in the checkpoint.
- If you call `client.threads.update_state`, you **must** use the new `checkpoint_id` returned by that call to resume execution.

### AVOID

- Do not pass new `input` when resuming from a `checkpoint_id`. This will result in an error.
- Do not assume a `checkpoint_id` is static after a state update. `update_state` creates a new checkpoint and thus a new ID.
- Avoid modifying the original execution history. The time-travel mechanism is designed to create new, distinct forks, preserving a full audit trail.

## API Reference

A minimal reference for core `langgraph_sdk` client methods.

| Method                                  | Description                                                                                             |
| :-------------------------------------- | :------------------------------------------------------------------------------------------------------ |
| `client.threads.create()`               | Creates a new, empty thread. Returns thread object with `thread_id`.                                    |
| `client.threads.get_history(thread_id)` | Retrieves all checkpoint states for a thread, sorted from most to least recent.                         |
| `client.threads.update_state(...)`      | Updates the state at a specific `checkpoint_id`, creating and returning a new checkpoint configuration. |
| `client.runs.wait(thread_id, ...)`      | Invokes the graph and waits for the final result.                                                       |
| `client.runs.stream(thread_id, ...)`    | Invokes the graph and streams back all intermediate events and node outputs.                            |

### Key Arguments

- `thread_id`: `str` - The identifier for the execution history.
- `assistant_id`: `str` - The identifier of the deployed graph to run.
- `input`: `dict` - The initial input for a new run. Must be `None` when resuming.
- `checkpoint_id`: `str` - The specific checkpoint to resume execution from.

## Resources

- [Time travel using the server API](https://docs.langchain.com/langsmith/human-in-the-loop-time-travel)
