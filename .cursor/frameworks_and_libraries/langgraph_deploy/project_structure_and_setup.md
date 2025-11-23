# LangGraph Deploy Documentation

This document provides guidelines for interacting with, configuring, and using LangGraph Deploy.

## Core Concepts

A LangGraph application consists of four main components:

1.  **Graphs**: The core application logic, implemented as one or more compiled `StateGraph` instances.
2.  **Configuration (`langgraph.json`)**: A JSON file specifying dependencies, graphs, and environment variables for a deployable agent.
3.  **Dependencies (`pyproject.toml`)**: A file specifying required packages.
4.  **Environment Variables (`.env`)**: An optional file for specifying environment variables.

## Project Structures

### Standard Project

```
my-app/
├── my_agent/
│   ├── __init__.py
│   └── agent.py
├── .env
├── langgraph.json
└── pyproject.toml
```

### Monorepo Project

For projects with multiple agents and shared code.

```
monorepo/
├── agents/
│   ├── agent-one/
│   │   ├── agent_one/
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── langgraph.json
│   │   └── pyproject.toml
│   └── agent-two/
│       └── ...
└── packages/
    └── shared-utils/
        ├── pyproject.toml
        └── shared_utils/
            ├── __init__.py
            └── tools.py
```

## Configuration (`langgraph.json`)

This file is the central configuration for a _single_ deployable agent. It must be placed at the same level or higher than the agent's application code. In a monorepo, each agent has its own `langgraph.json`.

### `dependencies`

An array of strings specifying dependencies. This includes PyPI packages and paths to local packages. For the agent's own code to be installed, include `.` in the list.

```json
{
  "dependencies": ["langchain_openai", "."]
}
```

### `graphs`

An object mapping a unique name to the graph object's location, in the format `./path/to/file.py:variable_name`.

```json
{
  "graphs": {
    "my_agent": "./my_agent/agent.py:graph"
  }
}
```

### `env`

A string specifying the path to your environment variables file.

```json
{
  "env": ".env"
}
```

## Dependency Management (`pyproject.toml`)

Use `pyproject.toml` to define project metadata and dependencies.

### Application `pyproject.toml`

Defines the agent's package. The `packages` key under `[tool.hatch.build.targets.wheel]` specifies which directories to include.

```toml
[project]
name = "my-agent"
version = "0.0.1"
dependencies = [
    "langgraph>=0.6.0",
]

[tool.hatch.build.targets.wheel]
packages = ["my_agent"]
```

## Monorepo Support

- **Structure**: Isolate agents and shared packages into their own directories (e.g., `/agents`, `/packages`).
- **Configuration**: Each agent directory must contain its own `langgraph.json` and `pyproject.toml`.
- **Dependencies**: In an agent's `langgraph.json`, reference shared local packages using relative paths.

### Example Monorepo `langgraph.json` for `agent-one`

```json
{
  "dependencies": [".", "../../packages/shared-utils"],
  "graphs": {
    "agent_one": "./agent_one/agent.py:graph"
  }
}
```

The build process correctly handles the relative path to install the `shared-utils` package.

## CLI Commands

### `langgraph build`

Creates a deployable Docker image from your agent's configuration. Run this command from the same directory as your agent's `langgraph.json`.

### `langgraph dev`

Starts a local development server for your agent. This server hosts the graphs defined in `langgraph.json` and automatically reloads on code changes, enabling rapid testing and iteration.

## Guidelines and Best Practices

### Must Do:

- Place `langgraph.json` in the root directory of each deployable agent.
- In `pyproject.toml`, correctly specify the package directory under `[tool.hatch.build.targets.wheel]`.
- Include `.` in `langgraph.json` dependencies to install the agent's own code.
- In a monorepo, use relative paths in `langgraph.json` to link to shared local packages.
- Ensure each local package (agent or shared) has a `pyproject.toml` file.

### Avoid:

- Placing a single `langgraph.json` at the monorepo root for all agents.
- Using absolute paths for local dependencies.
- Forgetting to list local dependencies (like shared packages or the agent itself) in `langgraph.json`.

## References

https://docs.langchain.com/langsmith/local-server
https://docs.langchain.com/langsmith/application-structure
https://docs.langchain.com/langsmith/setup-pyproject
https://docs.langchain.com/langsmith/monorepo-support
