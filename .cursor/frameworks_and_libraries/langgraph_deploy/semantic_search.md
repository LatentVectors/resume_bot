# LangGraph Deploy Interaction & Configuration Guide

This document provides concise guidelines for an LLM to interact with, configure, and use LangGraph Deploy.

## 1. Core Concepts

LangGraph Deploy allows you to host and interact with `langgraph` applications as persistent, scalable services. Key components include:

- **`langgraph.json`**: The central configuration file for your deployment. It defines the application graph, dependencies, and persistent store settings.
- **Store (`BaseStore`)**: A persistent, cross-thread key-value store. It can be configured for semantic search, enabling stateful and context-aware agents.
- **`RemoteGraph`**: An SDK object for interacting with a deployed LangGraph application from a client.
- **Agent Server**: The runtime environment that hosts the deployed graph.

## 2. Configuration (`langgraph.json`)

Configuration is critical for defining deployment behavior. Pay close attention to the `store` object.

### Semantic Search Configuration

To enable semantic search over the application's persistent state, configure the `store.index` object.

**DO**:

- Specify `embed`, `dims`, and `fields`.
- Ensure `dims` matches the output dimension of your embedding model.
- Use `["$"]` to index all fields, or specify a JSONPath for targeted indexing (e.g., `["messages[*].content"]`).

**Example `langgraph.json` for OpenAI embeddings:**

```json
{
  "store": {
    "index": {
      "embed": "openai:text-embedding-3-small",
      "dims": 1536,
      "fields": ["$"]
    }
  }
}
```

**AVOID**:

- Mismatched embedding dimensions.
- Forgetting to install required dependencies (e.g., `langchain-openai`).

### Custom Embeddings

For non-standard or private embedding models, provide a path to an async function.

**DO**:

- Specify the function path in `embed` as `"path/to/file.py:function_name"`.
- The function MUST be `async`, accept `list[str]`, and return `list[list[float]]`.

**Example `langgraph.json`:**

```json
{
  "store": {
    "index": {
      "embed": "my_embeddings.py:aembed_texts",
      "dims": 768,
      "fields": ["content"]
    }
  }
}
```

**Example `my_embeddings.py`:**

```python
# my_embeddings.py
import aiohttp

async def aembed_texts(texts: list[str]) -> list[list[float]]:
    # Custom logic to call your embedding model API
    async with aiohttp.ClientSession() as session:
        # ... implementation ...
        return embeddings
```

## 3. Interaction

Interaction occurs in two primary ways: within a graph's nodes or from an external client via an SDK.

### 3.1. Within Graph Nodes (`BaseStore`)

Nodes in your graph receive a `store: BaseStore` object to interact with the persistent state.

**`store.search(namespace, query, limit)`**:

- `namespace: tuple[str, ...]`: A tuple to logically partition data. **MUST** be used. E.g., `("user_facts", user_id)`.
- `query: str`: The text to search for.
- `limit: int`: The maximum number of results to return.

**DO**:

- Use namespaces to organize data by type and owner (e.g., user ID, session ID).
- Perform semantic searches to retrieve relevant context for the current task.

**Example Node:**

```python
from langgraph.prebuilt import ToolNode
from typing import TypedDict

class State(TypedDict):
    # ...
    context: list[str]

def search_memory(state: State, *, store: BaseStore):
    # Retrieve facts relevant to the user's latest message
    # Assumes last message is in state["messages"][-1].content
    results = store.search(
        namespace=("memory", "facts"),
        query=state["messages"][-1].content,
        limit=5
    )
    return {"context": [r.value for r in results]}
```

### 3.2. External Interaction (`RemoteGraph` & `langgraph_sdk`)

Use the `langgraph_sdk` for asynchronous client-side interaction with a deployed graph.

**`get_client()`**:

- Initializes and returns an async client. Configure it with environment variables (`LANGGRAPH_API_URL`, `LANGGRAPH_API_KEY`).

**`client.store.search_items(namespace, query, limit)`**:

- Performs a semantic search on the deployment's store.
- Arguments are identical to the `store.search()` method.
- The method is `async` and must be awaited.

**DO**:

- Use `async` functions to call SDK methods.
- Handle authentication and endpoint configuration via environment variables.

**Example Client Code:**

```python
from langgraph_sdk import get_client
import asyncio

async def query_remote_store(ns, q, lim):
    client = get_client()
    results = await client.store.search_items(
        namespace=ns,
        query=q,
        limit=lim
    )
    print(results)

# Run the async function
# asyncio.run(query_remote_store(("memory", "facts"), "user query", 3))
```

**AVOID**:

- Calling async SDK methods in a synchronous context without `asyncio.run()` or a running event loop.
- Hardcoding API keys or URLs. Use environment variables.

## 4. Key Guidelines Summary

### MUST DO

1.  **Configure `langgraph.json`**: Properly define your graph, dependencies, and store settings, especially for semantic search (`embed`, `dims`, `fields`).
2.  **Use Namespaces**: Always organize store data using a `namespace` tuple in `store.search()` and `client.store.search_items()`.
3.  **Use Async for SDK**: All interactions with the `langgraph_sdk` must be asynchronous. Use `await`.
4.  **Match Dimensions**: Ensure the `dims` in `langgraph.json` exactly matches the output dimension of your `embed` model.
5.  **Use Environment Variables**: For client-side configuration (`LANGGRAPH_API_URL`, `LANGGRAPH_API_KEY`).

### AVOID

1.  **Ignoring Namespaces**: Do not write to the store without a clear, hierarchical namespace; this leads to data collision and retrieval errors.
2.  **Mismatched Config**: Do not deploy with an embedding model whose output dimension differs from the `dims` value in `langgraph.json`.
3.  **Synchronous SDK Calls**: Do not call `langgraph_sdk` methods without `await`.
4.  **Hardcoding Credentials**: Do not embed API keys or sensitive URLs directly in your code.

## Resources

- https://docs.langchain.com/langsmith/semantic-search
