# LangGraph Deploy: Dynamic Graph Rebuilding

This document provides guidelines for configuring and using dynamic graph rebuilding in LangGraph Deploy.

## Overview

LangGraph Deploy allows for two modes of graph instantiation: static and dynamic.

1.  **Static Graph**: A single, compiled graph instance is used for all runs. This is the default behavior.
2.  **Dynamic Graph (Rebuild)**: A new graph instance is constructed for each run based on the provided configuration. This enables per-run customization of the graph's state, nodes, or structure.

## Static Graph Configuration

To deploy a static graph, define a `CompiledStateGraph` instance in your Python module.

- **`openai_agent.py`**

  ```python
  from langchain_openai import ChatOpenAI
  from langgraph.graph import END, START, MessageGraph

  model = ChatOpenAI(temperature=0)
  graph_workflow = MessageGraph()
  graph_workflow.add_node("agent", model)
  graph_workflow.add_edge("agent", END)
  graph_workflow.add_edge(START, "agent")
  agent = graph_workflow.compile()
  ```

Your `langgraph.json` must point directly to this compiled `agent` variable.

- **`langgraph.json`**
  ```json
  {
    "dependencies": ["."],
    "graphs": {
      "openai_agent": "./openai_agent.py:agent"
    },
    "env": "./.env"
  }
  ```

## Dynamic Graph Rebuilding

To rebuild a graph on each run, you must provide a graph-making function instead of a pre-compiled graph instance.

### The Graph-Making Function

This function is responsible for constructing and returning a graph instance based on runtime configuration.

**Function Signature:**
The function MUST accept a single argument: `config: RunnableConfig`.

**Configuration Access:**
Access runtime parameters from the `config` object. Custom parameters are typically passed within the `configurable` dictionary.

- **`openai_agent.py` with `make_graph` function**

  ```python
  from langchain_core.runnables import RunnableConfig
  # ... other necessary imports for graph construction

  # Define different graph construction functions
  def make_default_graph():
      # ... returns a compiled graph instance
      pass

  def make_alternative_graph():
      # ... returns a different compiled graph instance
      pass

  # Define the primary graph-making function
  def make_graph(config: RunnableConfig):
      """
      Dynamically selects and returns a graph based on user_id.
      """
      user_id = config.get("configurable", {}).get("user_id")

      if user_id == "1":
          return make_default_graph()
      else:
          return make_alternative_graph()
  ```

### Dynamic Graph `langgraph.json` Configuration

Update `langgraph.json` to point to the graph-making function, not a variable. The path format is `./path/to/module.py:function_name`.

- **`langgraph.json`**
  ```json
  {
    "dependencies": ["."],
    "graphs": {
      "openai_agent": "./openai_agent.py:make_graph"
    },
    "env": "./.env"
  }
  ```

## Core Guidelines

### MUST

- To enable per-run graph customization, implement a function that returns a compiled graph.
- The graph-making function MUST accept one argument: `config: RunnableConfig`.
- In `langgraph.json`, the path for a dynamic graph MUST point to the graph-making function (e.g., `module.py:function_name`).
- Extract runtime configuration from the `configurable` field of the `RunnableConfig` object.

### AVOID

- Do not point to a static graph instance in `langgraph.json` if the graph structure or state needs to change at runtime.
- Avoid implementing complex conditional logic inside a single monolithic graph if you can achieve the same result by dynamically constructing and returning different, simpler graphs.

## Resources

- [Rebuild graph at runtime](https://docs.langchain.com/langsmith/graph-rebuild)
