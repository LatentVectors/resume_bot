# LangGraph Deploy Interaction Guide

This document provides concise guidelines for an LLM to interact with a deployed LangGraph graph via the LangSmith Deployment API.

## 1. Overview

LangGraph Deploy allows running a compiled graph on a server. Interaction is performed via the `langgraph-sdk`, which connects to a deployment endpoint. The primary mode of interaction is streaming outputs from a run.

## 2. Core Interaction Workflow

The standard workflow involves three steps:

1.  **Get Client**: Authenticate and connect to the deployment URL.
2.  **Create Thread**: Establish a persistent state container for the run.
3.  **Stream Run**: Execute the graph with inputs and stream back the results.

```python
from langgraph_sdk import get_client

# 1. Get Client
client = get_client(url="<DEPLOYMENT_URL>", api_key="<API_KEY>")

# Specify the deployed graph to run
assistant_id = "my-graph-name"
inputs = {"topic": "ice cream"}

# 2. Create Thread
thread = await client.threads.create()
thread_id = thread["thread_id"]

# 3. Stream Run
async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input=inputs,
    stream_mode="updates"
):
    print(chunk.data)
```

## 3. Client Configuration

### `langgraph_sdk.get_client(...)`

Creates a client to interact with a deployed LangGraph.

- `url` (str): **Required**. The URL of the deployment.
- `api_key` (str, Optional): API key for authentication.

## 4. Streaming Runs

The primary method for graph execution is `client.runs.stream`.

### `client.runs.stream(...)`

Creates a run and streams its outputs.

- `thread_id` (str | None): **Required**. The ID of the thread to run against. For stateless execution where state is not persisted, pass `None`.
- `assistant_id` (str): **Required**. The name of the deployed graph to execute.
- `input` (dict): **Required**. The input dictionary for the graph's initial state.
- `stream_mode` (str | list[str]): **Required**. Specifies the type of data to stream. See "Streaming Modes" below. Defaults to `"updates"`.
- `stream_subgraphs` (bool, Optional): Set to `True` to include outputs from subgraphs in the stream. Defaults to `False`.

## 5. Streaming Modes

The `stream_mode` parameter controls the content of the streamed chunks.

| Mode             | Description                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `updates`        | Streams only the updates to the graph state after each node executes. Includes the node name. |
| `values`         | Streams the full graph state after each step.                                                 |
| `messages-tuple` | Streams LLM tokens as a `(message_chunk, metadata)` tuple. Use for real-time chat output.     |
| `debug`          | Streams maximum information, including node names and the full state at each step.            |
| `events`         | Streams all internal events, useful for complex debugging or migration from LCEL.             |
| `custom`         | Streams only data explicitly sent via custom events from within the graph.                    |

To receive multiple types of data, provide a list of modes (e.g., `stream_mode=["updates", "messages-tuple"]`). The output will be tuples of `(mode, chunk)`.

## 6. Advanced Usage

### Stateless Runs

To execute a graph without creating or using a persistent thread, pass `None` for the `thread_id`. This is useful for single-turn interactions.

```python
async for chunk in client.runs.stream(None, assistant_id, input=inputs):
    print(chunk.data)
```

### Joining an Existing Run

To stream outputs from an already active run, use `client.runs.join_stream`. Note that you will only receive outputs generated _after_ you join; prior outputs are not buffered.

- `client.runs.join_stream(thread_id, run_id)`

## 7. Guidelines

### DO

- **Use `async for`**: The `stream` method returns an async iterator.
- **Specify `stream_mode`**: Choose the mode that provides the minimum data you need. `updates` is efficient for state tracking; `messages-tuple` is essential for streaming chat responses.
- **Handle Thread State**: Create a thread for conversational history. Use `thread_id` to continue a conversation.
- **Use Stateless Runs for Simplicity**: For non-conversational tasks, use `thread_id=None` to avoid managing threads.

### AVOID

- **Blocking Calls**: Do not use blocking calls when a streaming alternative is available.
- **Ignoring `stream_mode`**: The default mode might not be what you need. Explicitly set it.
- **Joining a Stream Late**: Remember that `join_stream` does not provide historical output.

---

## Resources

- https://docs.langchain.com/langsmith/streaming
