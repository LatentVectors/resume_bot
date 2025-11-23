# LangGraph Deploy Guide for LLMs

This document provides comprehensive guidelines for creating, configuring, and deploying graphs using LangGraph Deploy.

## 1. Overview

LangGraph Deploy is a service for deploying LangGraph graphs as robust, scalable APIs on LangSmith. It automates the process of packaging, versioning, and hosting your stateful agentic applications.

## 2. Project Structure

A deployable LangGraph project requires a specific file structure. Use `langgraph new <project-name>` to generate a new project with the required layout.

```text
my-graph/
├── app/
│   ├── __init__.py
│   └── graph.py       # Your graph definition
├── tests/
│   ├── __init__.py
│   └── test_graph.py  # Tests for your graph
└── pyproject.toml     # Project dependencies
```

**Key Files:**

- `app/graph.py`: Contains the graph definition. This file **must** define a variable named `deployable`.
- `pyproject.toml`: Defines project metadata and dependencies. LangGraph Deploy uses this to install necessary packages in the runtime environment.

## 3. Defining the Deployable Graph

The core of your project is the `app/graph.py` file. It must contain a variable named `deployable` which is an instance of your `CompiledGraph`.

**`app/graph.py` Requirements:**

1.  **Import necessary libraries:** `StateGraph`, `START`, `END`, etc.
2.  **Define a State `TypedDict`:** This specifies the structure of your graph's state.
3.  **Define graph nodes:** These are the functions or callables that perform actions.
4.  **Construct the graph:** Use `StateGraph` to add nodes and edges.
5.  **Compile the graph:** Call `.compile()` on your graph instance.
6.  **Assign to `deployable`:** The compiled graph object **must** be assigned to a variable named `deployable`.

```python
# app/graph.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import START

class MyState(TypedDict):
    input: str
    output: Annotated[list[str], operator.add]

def node_one(state: MyState):
    # ... logic ...
    return {"output": ["result"]}

# Define the graph
builder = StateGraph(MyState)
builder.add_node("node_one", node_one)
builder.add_edge(START, "node_one")
builder.add_edge("node_one", END)

# The compiled graph must be assigned to a variable named "deployable"
deployable = builder.compile()
```

## 4. Configuration

Project configuration is managed through `pyproject.toml`. Dependencies are specified under `[project]`. LangGraph Deploy uses this file to create the execution environment.

```toml
# pyproject.toml
[project]
name = "my-graph"
version = "0.1.0"
dependencies = [
    "langgraph",
    # Add other required packages here
]
```

## 5. Command-Line Interface (CLI)

The `langgraph` CLI is the primary tool for managing deployments.

- **`langgraph new <project-name>`**

  - Creates a new LangGraph project with the standard directory structure.

- **`langgraph deploy`**
  - Deploys your graph to LangSmith.
  - Must be run from the root of your project directory (e.g., `my-graph/`).
  - LangSmith API keys must be configured in your environment.
  - **Arguments:**
    - `--graph-id <graph_id>`: (Required) A unique identifier for your graph. This is used to track versions of the same graph.
    - `--tags <tag1> <tag2>`: (Optional) Assign tags to the deployment for organization. The latest deployment for a given tag can be invoked.
    - `--metadata <key>=<value>`: (Optional) Attach key-value metadata.
    - `--skip-public`: (Optional) Makes the deployment private by default.

## 6. API Interaction

Once deployed, your graph is accessible via a REST API. You can interact with it using the `langsmith` SDK or any HTTP client.

### Using `langsmith` SDK

The `LangSmith` client provides a convenient way to invoke your graph.

```python
from langsmith import Client

client = Client()

# Get a runnable for the latest deployment with a specific tag
runnable = client.get_runnable(
    graph_id="my-graph-id",
    tag="prod" # or use deployment_id="..."
)

# Invoke the graph
# The input format must match your graph's input schema
# The config can be used to manage threads and recursion
result = runnable.invoke(
    {"input": "some value"},
    config={"configurable": {"thread_id": "thread-123"}}
)

# Stream events from the graph
for chunk in runnable.stream(
    {"input": "some value"},
    config={"configurable": {"thread_id": "thread-456"}}
):
    print(chunk)
```

**Key `get_runnable` Arguments:**

- `graph_id: str`: The unique ID you deployed with.
- `deployment_id: str | None`: The specific deployment version to run.
- `tag: str | None`: The tag of the deployment to run (e.g., "prod"). If a tag is used, the latest deployment with that tag is selected.

### State Management

LangGraph Deploy manages state based on the `thread_id` provided in the `configurable` dictionary of the request's `config`. Each unique `thread_id` corresponds to a persistent stateful conversation.

## 7. Guidelines & Best Practices

### Must Do:

- **Assign to `deployable`**: Your compiled graph object **must** be named `deployable` in `app/graph.py`.
- **Define Dependencies**: Accurately list all required Python packages in `pyproject.toml`.
- **Use `thread_id`**: Always pass a `thread_id` in the `config` object when invoking the API to manage conversation state correctly.
- **Version with Tags**: Use tags (`--tags prod`) to manage different versions of your deployment (e.g., staging, production).
- **Structure Your Code**: Adhere to the `langgraph new` project structure.

### Avoid:

- **Local File System Access**: Do not rely on reading from or writing to the local file system. The runtime environment is ephemeral.
- **Global State**: Avoid using global variables in your node functions. State should be managed exclusively through the `State` object.
- **Hardcoding Secrets**: Do not hardcode API keys or other secrets in your code. Use environment variables, which can be configured in the LangSmith settings.
- **Large Dependencies**: Keep your `pyproject.toml` dependencies minimal to ensure faster deployment and cold start times.

---

### Resources

- https://docs.langchain.com/langsmith/cicd-pipeline-example
