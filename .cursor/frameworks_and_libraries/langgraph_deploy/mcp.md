# LangGraph Deploy: LLM Interaction Guidelines

This document provides comprehensive guidelines for interacting with, configuring, and using LangGraph Deploy. Follow these instructions precisely.

## 1. Overview

LangGraph Deploy allows you to run LangGraph graphs as persistent services. You interact with it primarily through the `langgraph-cli` command-line tool and a LangSmith+ account. The core workflow is: define your graph, configure metadata, upload it, and then interact with the deployed service via an API.

Deployments can be public or private. Public deployments are accessible to anyone with the URL, while private deployments require an API key from a project in the same LangSmith organization.

## 2. Core Concepts & Project Structure

Your project must have a specific structure for successful deployment.

- **`graph.py`**: This file is mandatory. It must contain a function named `get_graph` that returns your compiled `StateGraph` or `Graph` instance. This function can optionally accept a `config` dictionary.

  ```python
  # graph.py
  from langgraph.graph import StateGraph

  def get_graph(config: dict) -> StateGraph:
      # Define and compile your graph here
      workflow = StateGraph(State)
      # ... add nodes and edges
      app = workflow.compile()
      return app
  ```

- **`pyproject.toml`**: This file is mandatory. It must contain a `[tool.langgraph]` section specifying the module path to your graph. It also manages dependencies.

  ```toml
  # pyproject.toml
  [project]
  name = "my-graph-project"
  version = "0.1.0"
  dependencies = [
      "langgraph",
      "langchain-openai",
      # other required packages
  ]

  [tool.langgraph]
  # Path to the directory containing graph.py
  graph_path = "my_package.graph:get_graph"
  ```

- **`Dockerfile` (Optional)**: If your project has system-level dependencies (e.g., `ffmpeg`, `poppler-utils`), you can provide a custom `Dockerfile` for the build environment. The CLI will use it instead of the default.

## 3. `langgraph-cli` Usage

The `langgraph-cli` is the primary tool for managing deployments. Ensure you have `langgraph-cli` installed (`pip install langgraph-cli`).

### Configuration

Before using the CLI, set these environment variables:

```bash
export LANGSMITH_API_KEY="ls__..."
export LANGSMITH_TENANT_ID="your-tenant-id"
```

- The `LANGSMITH_TENANT_ID` is found in your LangSmith organization's settings page URL (`https://smith.langchain.com/o/{tenant-id}/`).

### Key Commands

- **`langgraph-cli app new`**: Initialize a new LangGraph project with the required structure.

- **`langgraph-cli app upload`**: Uploads and deploys your graph.

  - `graph_id`: A unique identifier for your graph (e.g., `my-agent`).
  - `--tag`: (Optional) An alias for a specific version, like `dev` or `prod`. Useful for CI/CD. Defaults to a unique build ID.

  ```bash
  langgraph-cli app upload my-agent --tag prod
  ```

- **`langgraph-cli app ls`**: List all uploaded graphs in your organization.

- **`langgraph-cli app get <graph_id>`**: Retrieve details for a specific graph.

- **`langgraph-cli app download <graph_id>`**: Download the code bundle for a specific graph version.

- **`langgraph-cli build ls <graph_id>`**: List all builds (versions) for a given graph.

- **`langgraph-cli deployment ls <graph_id>`**: List all active deployments for a graph.

- **`langgraph-cli deployment update <graph_id> --build-id <build_id> --tag <tag>`**: Promote a specific build to a tag (e.g., promote a staging build to `prod`).

## 4. API Interaction

Once deployed, you interact with your graph via the LangSmith SDK.

### `RemoteRunnable`

The primary interface is `RemoteRunnable`. It mirrors the standard LangChain runnable interface.

- **URL Construction**: The URL for a `RemoteRunnable` is:
  `https://{api_url}/graphs/{graph_id}/{tag}`

  - `api_url` is typically `api.smith.langchain.com`.
  - `{graph_id}` is your unique graph identifier.
  - `{tag}` is the deployment tag (e.g., `prod`). Defaults to the latest build if omitted.

- **Authentication**:
  - **Private Graphs**: Pass your LangSmith API key via the `langchain_api_key` argument.
  - **Public Graphs**: No key is required.

### Invocation Methods

Use standard `Runnable` methods to interact with the deployed graph.

```python
from langgraph.prebuilt import RemoteRunnable

# For a private graph
remote_graph = RemoteRunnable(
    "https://api.smith.langchain.com/graphs/my-agent/prod",
    langchain_api_key="YOUR_LANGSMITH_API_KEY"
)

# For a public graph
# remote_graph = RemoteRunnable("https://api.smith.langchain.com/graphs/public-agent/prod")

# Invoke the graph with input
result = remote_graph.invoke({"input": "Hello!"})

# Stream intermediate steps
for chunk in remote_graph.stream({"input": "What is LangGraph?"}):
    print(chunk)

# Stream final output only
for chunk in remote_graph.stream({"input": "What is LangGraph?"}, stream_mode="values"):
    print(chunk)
```

- **`invoke(input, config)`**: Executes the graph and returns the final result.
- **`batch(inputs, config)`**: Executes the graph on a list of inputs.
- **`stream(input, config, stream_mode)`**: Streams outputs.
  - `stream_mode="values"`: Returns only the final output state.
  - `stream_mode="updates"`: Returns a stream of writes (diffs) for each step. This is the default.
  - `stream_mode="states"`: Returns the full state after each step.
- **`astream(...)`**: Async versions of all methods are available.

### Passing Configuration

To pass runtime configuration (e.g., credentials, parameters) to your `get_graph` function, use the `configurable` field in the `config` argument.

```python
# Pass a value for the 'model_name' key in the config dict
remote_graph.invoke(
    {"messages": [("user", "hi")]},
    config={"configurable": {"model_name": "gpt-4"}}
)
```

## 5. Guidelines

### MUST DO

- **Pin Dependencies**: Specify exact versions of all libraries in `pyproject.toml` to ensure reproducible builds.
- **Structure Correctly**: Ensure your project contains `pyproject.toml` and a `graph.py` with a `get_graph` function.
- **Set Environment Variables**: Always set `LANGSMITH_API_KEY` and `LANGSMITH_TENANT_ID` before using `langgraph-cli`.
- **Use `configurable`**: Pass dynamic configuration, especially secrets, into your graph at runtime using the `configurable` key in the `invoke`/`stream` config.

### AVOID

- **Hardcoding Secrets**: Do not store API keys or other secrets directly in your `graph.py` file. Pass them at runtime.
- **Using Relative Paths**: Avoid file system operations with relative paths, as the execution environment is ephemeral. If you need to load data, include it in your project directory and use paths relative to your `graph.py` file.
- **Ignoring `pyproject.toml`**: The build process relies entirely on `pyproject.toml` to install dependencies. Do not assume packages are pre-installed.
- **Large Asset Files**: Avoid including large model weights or data files in your uploaded bundle. Load them from external sources at runtime if possible.

---

### Resources

- <https://langchain-ai.github.io/langgraph/deployment/>
- <https://langchain-ai.github.io/langgraph/deployment/cli/>
- <https://langchain-ai.github.io/langgraph/deployment/api/>
- <https://docs.langchain.com/langsmith/server-mcp>
