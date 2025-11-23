# LangGraph Deploy Interaction Guide

This document provides comprehensive guidelines for an LLM to interact with a deployed LangGraph graph using the `RemoteGraph` client.

## 1. Overview

`RemoteGraph` is a client-side interface that interacts with a deployed LangGraph graph as if it were a local `CompiledGraph`. It provides API parity, enabling the use of methods like `invoke()`, `stream()`, and `get_state()` for both local development and production environments.

**Primary Use Cases:**

- **Separation of Concerns:** Build and test graphs locally, then call them remotely in production using the same interface.
- **Stateful Conversations:** Persist and fetch conversation state across multiple calls using a `thread_id`.
- **Subgraph Composition:** Embed deployed graphs as nodes within another graph to create modular, multi-agent workflows.

## 2. Core Concepts & API

The primary interface is the `RemoteGraph` class.

### 2.1 Initialization

A `RemoteGraph` instance connects to a specific graph or assistant on a running Agent Server.

```python
from langgraph.pregel.remote import RemoteGraph

# url is the URL of your LangGraph deployment
# name is the graph name or assistant_id
remote_graph = RemoteGraph(name="my_graph_name", url="<DEPLOYMENT_URL>")
```

**Key `RemoteGraph` Initialization Arguments:**

- `name` (str): **Required.** The name of the graph or a specific `assistant_id` to interact with.
- `url` (str): The URL of the deployment. If provided, both sync and async clients are created automatically.
- `client` (LangGraphClient): An asynchronous client instance for `ainvoke`, `astream`, etc.
- `sync_client` (SyncLangGraphClient): A synchronous client instance for `invoke`, `stream`, etc.

**MUST:** You must provide `name` and one of (`url`, `client`, `sync_client`). `client` or `sync_client` arguments take precedence over `url`.

**AVOID:** Do not use `RemoteGraph` to call a graph on the _same_ deployment. This can cause deadlocks. Use local graph composition for intra-deployment calls.

### 2.2 Invocation

`RemoteGraph` implements the `Runnable` interface, mirroring `CompiledGraph`.

- `invoke(input, config=None)`: Synchronously call the graph with a single input and get a single output.
- `ainvoke(input, config=None)`: Asynchronously call the graph.
- `stream(input, config=None)`: Synchronously stream back chunks of the graph output.
- `astream(input, config=None)`: Asynchronously stream back chunks.
- `batch(inputs, config=None)`: Execute on a list of inputs.

### 2.3 State Management

Manage the graph's state for persistent conversations.

- `get_state(config)`: Fetch the current state for a given `thread_id`.
- `update_state(config, values)`: Update the state for a `thread_id`. `values` is a dictionary to be merged into the current state.

## 3. Configuration and State Persistence

To maintain state across calls (e.g., for a conversation), use the `configurable` field in the `config` dictionary.

**MUST:** To persist state, pass a `thread_id` in the configuration. The server uses this ID to save and load checkpoints.

```python
# A unique identifier for the conversation thread
thread_id = "some-unique-thread-id"
config = {"configurable": {"thread_id": thread_id}}

# First call - state is created and saved
remote_graph.invoke(
    {"messages": [{"role": "user", "content": "My name is John."}]},
    config=config
)

# Second call - state is loaded, graph continues from where it left off
response = remote_graph.invoke(
    {"messages": [{"role": "user", "content": "What is my name?"}]},
    config=config
)

# You can also fetch the state directly
thread_state = remote_graph.get_state(config)
```

**MUST:** When using a `RemoteGraph` as a subgraph within a parent graph that uses a checkpointer, you **must** use UUIDs for `thread_id`.

## 4. Authentication

Authentication is handled via a LangSmith API key.

**MUST:** Provide the API key. This can be done in one of two ways:

1.  **Environment Variable (Recommended):** Set the `LANGSMITH_API_KEY` environment variable.
2.  **Directly:** Pass the key when creating a client.
    ```python
    from langgraph_sdk import get_sync_client
    client = get_sync_client(url="...", api_key="...")
    ```

## 5. Streaming

To receive intermediate outputs and logs from the graph execution, use the `stream` or `astream` methods.

```python
config = {"configurable": {"thread_id": "thread-123"}}
for chunk in remote_graph.stream({"messages": [{"role": "user", "content": "Hello"}]}, config=config):
    # Each chunk is a dictionary representing an event from the graph execution
    print(chunk)
```

## 6. Usage as a Subgraph

A `RemoteGraph` can be a node within a larger, local `StateGraph`. This allows for modular composition.

```python
from langgraph.graph import StateGraph, START
from langgraph.pregel.remote import RemoteGraph

# The remote graph acts as a node
remote_agent = RemoteGraph(name="agent", url="<DEPLOYMENT_URL>")

builder = StateGraph(...)
builder.add_node("child_agent", remote_agent)
builder.add_edge(START, "child_agent")
parent_graph = builder.compile()

# Invoking the parent graph will call the remote graph
parent_graph.invoke({"messages": [...]})
```

## 7. Rules and Best Practices

- **MUST:** Provide a `thread_id` in the `config` dictionary to persist state between calls.
- **MUST:** Ensure the `LANGSMITH_API_KEY` is correctly configured in the environment or passed to the client.
- **MUST:** Use UUIDs as `thread_id` if the `RemoteGraph` is a subgraph within a stateful parent graph.
- **AVOID:** Do not call a graph on the same deployment from which the call originates. This causes recursive calls and deadlocks.
- **AVOID:** Hardcoding credentials. Use environment variables for API keys.

---

### Resources

- https://docs.langchain.com/langsmith/use-remote-graph
