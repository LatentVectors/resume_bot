# LangGraph Deploy: Interaction & Configuration Guide

This guide provides instructions for interacting with and configuring graphs deployed via LangGraph Deploy. Follow these rules to manage, invoke, and add human-in-the-loop (HITL) interactions to your deployments.

## Core Concepts

- **Deployment**: A LangGraph graph uploaded to LangSmith, accessible via API. Managed by the `langgraph` CLI.
- **Thread**: Represents a single conversation or execution flow. Identified by `thread_id`.
- **Checkpoint**: A snapshot of a graph's state at a specific point in time. Enables resuming execution.
- **Feedback**: A mechanism for humans to provide input or corrections to a graph's execution. This is the core of Human-in-the-Loop.
- **State**: The current data within the graph's `State` object for a given thread.

## Deployment & Management

Deploying your graph is the first step. Your graph must be an instance of `CompiledGraph`.

### `langgraph.json` Configuration

A `langgraph.json` file in your project root configures deployments.

````json
{
  "graphs": {
    "my-graph-id": {
      "path": "my_package.my_module:my_graph_instance",
      "project_name": "optional-project-name"
    }
  }
}```

*   `my-graph-id`: A unique identifier for your graph deployment.
*   `path`: Python import path to your `CompiledGraph` instance.
*   `project_name`: (Optional) The LangSmith project to associate with runs.

### CLI Commands

Use the `langgraph` CLI to manage your deployments.

*   **Deploy/Upload**: `langgraph deploy`
*   **List Deployments**: `langgraph ls`
*   **Download Configuration**: `langgraph pull my-graph-id`

## Human-in-the-Loop (HITL) Interaction

Adding HITL allows a graph to pause, wait for human input, and then resume. This is achieved by including a `human` feedback key in the graph's output and updating the state with the feedback.

### Pausing for Feedback

To pause the graph and request feedback, a node must return a value that includes the key `"human"`.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

def call_model(state):
    # Node logic
    return {"messages": [("ai", "Response that needs verification.")]}

def human_approval(state):
    # This node is a gate. It returns a value with a "human" key,
    # causing the graph to pause and wait for feedback.
    return {"messages": [("human", "Please approve or provide feedback.", "tool_code", {"action": "human"} )]}

# Graph construction
workflow = StateGraph(AgentState)
workflow.add_node("call_model", call_model)
workflow.add_node("human_approval", human_approval)
# Define edges...
````

The graph will now pause at the `human_approval` step.

### Providing Feedback

Interact with a paused graph using the LangSmith SDK. Feedback is submitted for a specific `run_id` which corresponds to the paused step.

**DO**: Use the `client.create_feedback()` method.
**DO**: Set `key` to `"human"`.
**DO**: The `value` provided will be used to update the graph's state.

```python
from langsmith import Client

client = Client()

# The run_id of the step that is waiting for feedback
paused_run_id = "..."
feedback_value = "This looks great! Proceed."

client.create_feedback(
    run_id=paused_run_id,
    key="human",
    value=feedback_value,
)
```

### Resuming the Graph

After feedback is submitted, the graph's state is updated, and execution resumes automatically from the checkpoint. The feedback value is incorporated into the state, and the graph proceeds to the next node based on its conditional logic.

### Key `create_feedback` Arguments

- `run_id` (str): The ID of the specific run (trace) that is paused and awaiting feedback. **This is mandatory.**
- `key` (str): The feedback key. For HITL, this **must be `"human"`**.
- `value` (any): The payload to provide as feedback. This value will update the state. It can be a string, dict, or any other JSON-serializable type.
- `correction` (dict, optional): Alternative to `value` for structured corrections.
- `source` (str, optional): Metadata indicating the source of the feedback (e.g., "user_review").

## State and Checkpoints

- **DO**: Design your graph state (`AgentState` in the example) to accommodate human feedback.
- **DO**: Use checkpoints to manage the state of long-running or paused executions. The service handles this automatically.
- **AVOID**: Modifying state outside of the defined graph transitions. State updates should only occur via node returns or human feedback.

## Rules of Interaction

- **MUST**: Deploy a `CompiledGraph`.
- **MUST**: To enable HITL, have a node return a value containing the key `"human"`.
- **MUST**: Use `client.create_feedback` with `key="human"` to provide input to a paused graph.
- **AVOID**: Attempting to resume a graph without providing the required feedback. The graph will remain paused.
- **AVOID**: Submitting feedback to a run that is not in a paused state.

---

### Resources

- https://docs.langchain.com/langsmith/add-human-in-the-loop
